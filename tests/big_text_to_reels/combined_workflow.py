import os
import argparse
import datetime
import json
import logging
import random
import requests
import time
import tempfile
import io
from pathlib import Path
from typing import Dict, List, Any, Optional

# Google API imports
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import google_auth_oauthlib.flow

# Import modules from existing scripts
from analyze_google_doc import extract_doc_id_from_url, get_document_content, analyze_with_claude
from create_reel_scripts import ReelGenerator
from reel_picker import load_metadata_files, analyze_viral_potential, select_top_reels, save_top_reels, get_client

# YouTube OAuth credentials
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
TOKEN_FILE = "youtube_token.json"

# HeyGen API Key
HEYGEN_API_KEY = "NzYzODNmNTI5ODYyNGMyYTg1NzFhNTNmOWY4M2Q4OTYtMTc0MDczMjczOQ=="

# Service account path (hard-coded)
SERVICE_ACCOUNT_PATH = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/bustling-folio-439811-h8-539f8ab05fa7.json"

# Anthropic API key (hard-coded)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Set environment variable for Anthropic API
os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY

# Disable OAuthlib's HTTPS verification for local development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_google_doc(url: str, service_account_file: str) -> str:
    """Process a Google Doc and divide it into sections.
    
    Args:
        url: Google Doc URL
        service_account_file: Path to service account JSON file
    
    Returns:
        Path to the created analyzed text file
    """
    logger.info("Step 1: Analyzing Google Doc")
    logger.info(f"Extracting content from: {url}")
    
    # Extract document ID from URL
    doc_id = extract_doc_id_from_url(url)
    logger.info(f"Document ID: {doc_id}")
    
    # Get document content
    content = get_document_content(doc_id, service_account_file)
    logger.info(f"Retrieved {len(content)} characters from the document")
    
    # Analyze with Claude
    logger.info("Analyzing content with Claude...")
    analyzed_text = analyze_with_claude(content)
    
    # Create output file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(script_dir, f"analyzed_doc_{timestamp}.txt")
    
    # Write the analyzed text to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(analyzed_text)
    
    logger.info(f"Analysis written to {output_file}")
    return output_file

def create_reel_scripts(input_file: str, output_dir: str, 
                       overlap: int = 2, workers: int = 4, 
                       sections: Optional[str] = None, count: Optional[int] = None,
                       api_key: Optional[str] = None) -> str:
    """Create reel scripts from analyzed text file.
    
    Args:
        input_file: Path to analyzed text file
        output_dir: Directory to save output
        overlap: Number of paragraphs to include from adjacent sections
        workers: Maximum number of parallel workers
        sections: Specific section numbers to process (comma-separated)
        count: Number of reels to generate, starting from the beginning
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the metadata directory
    """
    logger.info("Step 2: Generating reel scripts")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Create generator
    generator = ReelGenerator(
        api_key=api_key,
        output_dir=output_dir,
        overlap_paragraphs=overlap
    )
    
    metadata_dir = os.path.join(output_dir, "metadata")
    
    # Process specific sections if requested
    if sections:
        section_numbers = [int(s.strip()) for s in sections.split(',')]
        
        # Read and parse the text
        text = generator.read_analyzed_text(input_file)
        
        # Split into sections
        sections_list = generator.split_into_sections(text)
        logger.info(f"Split text into {len(sections_list)} sections")
        
        # Extract titles and add context
        titled_sections = generator.extract_section_titles(sections_list)
        all_enriched_sections = generator.add_context_to_sections(titled_sections)
        
        # Filter sections by selected numbers
        enriched_sections = [s for s in all_enriched_sections if s['id'] in section_numbers]
        
        if not enriched_sections:
            logger.error(f"No valid sections found with numbers: {section_numbers}")
            return metadata_dir
            
        logger.info(f"Processing {len(enriched_sections)} selected sections: {section_numbers}")
        
        # Process selected sections in parallel
        processed_sections = generator.process_sections_parallel(enriched_sections, workers)
        
        # Save results
        generator.save_reel_scripts(processed_sections)
        
    elif count:
        # Read and parse the text
        text = generator.read_analyzed_text(input_file)
        
        # Split into sections
        sections_list = generator.split_into_sections(text)
        logger.info(f"Split text into {len(sections_list)} sections")
        
        # Extract titles and add context
        titled_sections = generator.extract_section_titles(sections_list)
        all_enriched_sections = generator.add_context_to_sections(titled_sections)
        
        # Take first N sections
        count = min(count, len(all_enriched_sections))
        enriched_sections = all_enriched_sections[:count]
        
        logger.info(f"Processing first {count} sections")
        
        # Process selected sections in parallel
        processed_sections = generator.process_sections_parallel(enriched_sections, workers)
        
        # Save results
        generator.save_reel_scripts(processed_sections)
    else:
        # Process all sections
        generator.process_file(
            input_filepath=input_file,
            max_workers=workers
        )
    
    logger.info(f"Reel scripts generated and saved to {output_dir}")
    return metadata_dir

def pick_top_reels(metadata_dir: str, top_n: int = 10, api_key: Optional[str] = None) -> str:
    """Select top reels based on viral potential.
    
    Args:
        metadata_dir: Directory containing metadata files
        top_n: Number of top reels to select
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the top reels directory
    """
    logger.info("Step 3: Picking top reels")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Define output directory
    parent_dir = os.path.dirname(metadata_dir)
    top_reels_dir = os.path.join(parent_dir, "top_reels")
    
    # Create output directory path
    Path(top_reels_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading metadata files from {metadata_dir}...")
    metadata_files = load_metadata_files(metadata_dir)
    logger.info(f"Loaded {len(metadata_files)} metadata files.")
    
    logger.info("Analyzing viral potential with Claude API...")
    # Need to set this temporarily because the module is imported
    os.environ["ANTHROPIC_API_KEY"] = api_key
    analyzed_reels = analyze_viral_potential(metadata_files, api_key)
    
    logger.info(f"Selecting top {top_n} viral reels...")
    top_reels = select_top_reels(analyzed_reels, top_n=top_n)
    
    logger.info(f"Saving top reels to {top_reels_dir}...")
    save_top_reels(top_reels, metadata_dir, top_reels_dir)
    
    logger.info("Top reels saved successfully")
    
    # Print summary of top reels
    logger.info("\nTop Viral Reels Summary:")
    for i, reel in enumerate(top_reels, 1):
        score = reel.get('viral_analysis', {}).get('score', 'N/A')
        title = reel.get('title', 'No title')
        filename = reel.get('filename', 'Unknown file')
        logger.info(f"{i}. {filename} - {title} (Score: {score})")
    
    return top_reels_dir

def final_reel_editing(top_reels_dir: str, edit_prompt: str, api_key: Optional[str] = None) -> str:
    """Apply final edits to top reels to improve engagement.
    
    Args:
        top_reels_dir: Directory containing top reels
        edit_prompt: Instructions for editing the reels
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the final reels directory
    """
    logger.info("Step 4: Final reel editing")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Get Anthropic client
    client = get_client(api_key)
    
    # Define output directory
    parent_dir = os.path.dirname(top_reels_dir)
    final_reels_dir = os.path.join(parent_dir, "final_reels")
    
    # Create output directory path
    Path(final_reels_dir).mkdir(parents=True, exist_ok=True)
    
    # Hooks to alternate between (from prompt)
    hook_variations = [
        "Это видео для тех, кто...",
        "Это история о том, как...",
        "А вы знали, что...",
        "Вряд ли вы мне поверите, но...",
        "У меня ушло несколько лет, чтобы...",
        "Короче...",
        "Самый классный в мире...",
        "Самый провальный...",
        "Самый лучший...",
        "Самый быстрый...",
        "Самый неэффективный способ..."
    ]
    
    # Load metadata files
    logger.info(f"Loading top reels from {top_reels_dir}...")
    metadata_files = []
    for filename in os.listdir(top_reels_dir):
        if filename.endswith('.json') and not filename.startswith('analysis_'):
            file_path = os.path.join(top_reels_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    metadata_files.append(data)
                    logger.info(f"Loaded {filename}")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    
    for i, reel_data in enumerate(metadata_files):
        # Select a random hook variant for each reel
        hook_variant = random.choice(hook_variations)
        
        # Get the script content
        script = reel_data.get('heygen_script', '')
        title = reel_data.get('title', '')
        
        # Create a prompt for Claude to edit the reel
        system_prompt = "You are an expert at editing social media scripts to maximize engagement. Make edits according to the guidelines provided, while preserving the core message and educational value."
        
        user_prompt = f"""Edit this Instagram reel script to make it more engaging and viral. 

CURRENT SCRIPT:
{script}

TITLE:
{title}

EDITING GUIDELINES:
{edit_prompt}

For this specific reel, use the following hook style:
{hook_variant}

Return ONLY the edited script text without any explanation or additional formatting. The script should be ready to use as-is and in Russian language.
"""
        
        try:
            # Call Claude to edit the script
            logger.info(f"Editing reel {i+1}/{len(metadata_files)}...")
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1500,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract content as string from the response
            edited_script = response.content[0].text.strip()
            
            # Update the reel data
            reel_data['original_script'] = script
            reel_data['heygen_script'] = edited_script
            
            # Save the edited reel metadata
            output_path = os.path.join(final_reels_dir, f"final_{i+1:02d}_{os.path.basename(reel_data.get('filename', f'reel_{i+1}.json'))}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(reel_data, f, ensure_ascii=False, indent=2)
            
            # Also save as a plain text file for heygen
            heygen_filename = f"final_heygen_{i+1:02d}.txt"
            heygen_path = os.path.join(final_reels_dir, heygen_filename)
            with open(heygen_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n{edited_script}")
            
            logger.info(f"Saved edited reel to {output_path}")
            
        except Exception as e:
            logger.error(f"Error editing reel {i+1}: {str(e)}")
    
    logger.info(f"Final reel editing completed. Edited reels saved to: {final_reels_dir}")
    return final_reels_dir

# ===== HeyGen and YouTube Integration Functions =====

def generate_heygen_video(metadata):
    """Generate a video using HeyGen API"""
    # Extract data from metadata
    script = metadata["heygen_script"]
    title = metadata["title"]
    
    # HeyGen API key and headers
    headers = {
        "X-Api-Key": HEYGEN_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Avatar and voice settings
    avatar_id = "866d2e167e8a43a38dcb4ddf96a52d97"
    voice_id = "aa6539b580bf4c9a93879977044e9a12"
    
    # API endpoint for video generation
    generate_url = "https://api.heygen.com/v2/video/generate"
    
    # Prepare the request payload
    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                    "scale": 2.2,
                    "position": {
                        "x": 0,
                        "y": -0.3
                    }
                },
                "voice": {
                    "type": "text",
                    "input_text": script,
                    "voice_id": voice_id
                },
                "background": {
                    "type": "color",
                    "value": "#000000"
                }
            }
        ],
        "dimension": {
            "width": 720,
            "height": 1280
        },
        "video_type": "vertical",
        "caption": True,
        "title": title
    }
    
    # Generate the video
    logger.info(f"Generating HeyGen video for: {title}")
    response = requests.post(generate_url, json=payload, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Error generating video: {response.text}")
        return None
    
    # Extract video ID from response
    response_data = response.json()
    if "data" not in response_data or "video_id" not in response_data["data"]:
        logger.error(f"Error: Invalid response format: {response_data}")
        return None
    
    video_id = response_data["data"]["video_id"]
    logger.info(f"Video generation started. Video ID: {video_id}")
    
    # Wait for video to complete
    video_url = check_heygen_video_status(video_id, headers)
    return video_url

def check_heygen_video_status(video_id, headers):
    """Check HeyGen video generation status"""
    video_status_url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    
    while True:
        response = requests.get(video_status_url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Error checking video status: {response.text}")
            return None
        
        status_data = response.json()
        if "data" not in status_data:
            logger.error(f"Error: Invalid status response format: {status_data}")
            return None
        
        status = status_data["data"]["status"]
        
        if status == "completed":
            video_url = status_data["data"]["video_url"]
            thumbnail_url = status_data["data"]["thumbnail_url"]
            logger.info(f"Video generation completed!")
            logger.info(f"Video URL: {video_url}")
            logger.info(f"Thumbnail URL: {thumbnail_url}")
            return video_url
        
        elif status == "processing" or status == "pending" or status == "waiting":
            logger.info("Video is still processing. Checking status again in 10 seconds...")
            time.sleep(10)
        
        elif status == "failed":
            error = status_data["data"].get("error", "Unknown error")
            logger.error(f"Video generation failed: {error}")
            return None
        
        else:
            logger.error(f"Unknown status: {status}")
            return None

def upload_to_drive(video_url, file_name, title):
    """Upload the video to Google Drive."""
    logger.info(f"Uploading video to Google Drive...")
    
    # Create a temporary file to store the downloaded video
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    
    # Download the video from the URL
    response = requests.get(video_url)
    if response.status_code != 200:
        logger.error(f"Error downloading video from URL: {response.status_code}")
        return None
    
    # Save temporarily
    with open(temp_file, "wb") as f:
        f.write(response.content)
    
    logger.info(f"Video downloaded to temporary file: {temp_file}")
    
    # Authenticate with Google Drive using hard-coded service account path
    scopes = ['https://www.googleapis.com/auth/drive']
    
    try:
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH, scopes=scopes)
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # Upload to Google Drive
        file_metadata = {
            'name': file_name,
            'description': title,
            'mimeType': 'video/mp4'
        }
        
        media = MediaFileUpload(temp_file, mimetype='video/mp4', resumable=True)
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id,webViewLink').execute()
        
        # Get Drive link
        file_id = file.get('id')
        web_link = file.get('webViewLink')
        
        logger.info(f"Video uploaded successfully to Google Drive!")
        logger.info(f"File ID: {file_id}")
        logger.info(f"Web link: {web_link}")
        
        # Set permissions to anyone with the link can view
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        drive_service.permissions().create(fileId=file_id, body=permission).execute()
        logger.info("Set permissions: Anyone with the link can view")
        
        return {'file_id': file_id, 'temp_path': temp_file}
    
    except Exception as e:
        logger.error(f"Error uploading to Drive: {str(e)}")
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return None

def get_authenticated_youtube_service():
    """Get an authenticated YouTube API service with token persistence."""
    credentials = None
    
    # Define OAuth scopes
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    
    # Create client secrets file from hardcoded values
    client_config = {
        "installed": {
            "client_id": YOUTUBE_CLIENT_ID,
            "project_id": "youtube-uploader",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": YOUTUBE_CLIENT_SECRET,
            "redirect_uris": ["http://localhost"]
        }
    }
    
    client_secrets_file = "client_secrets.json"
    with open(client_secrets_file, "w") as f:
        json.dump(client_config, f)
    
    try:
        # Use a simple token JSON file instead of pickle
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as token_file:
                token_data = json.load(token_file)
                credentials = Credentials.from_authorized_user_info(token_data)
                logger.info("Using stored YouTube credentials, no browser authentication needed")
        
        # If credentials don't exist or are invalid, we need to create new ones
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                logger.info("Refreshing expired credentials...")
                credentials.refresh(Request())
            else:
                logger.info("No valid YouTube credentials found. Need browser authentication (one-time setup)...")
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    client_secrets_file, scopes)
                
                # Use a random port to avoid conflicts
                port = random.randint(8080, 8089)
                credentials = flow.run_local_server(port=port)
                
                # Save credentials
                token_data = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes
                }
                
                with open(TOKEN_FILE, 'w') as token_file:
                    json.dump(token_data, token_file)
                logger.info(f"YouTube credentials saved to {TOKEN_FILE} for future use")
        
        return build("youtube", "v3", credentials=credentials)
    
    finally:
        # Clean up client secrets
        if os.path.exists(client_secrets_file):
            os.remove(client_secrets_file)

def download_from_drive(file_id):
    """Download video from Google Drive using service account authentication."""
    logger.info(f"Downloading video from Google Drive (File ID: {file_id})...")
    
    # Use service account credentials with hard-coded path
    scopes = ['https://www.googleapis.com/auth/drive.readonly']
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH, scopes=scopes)
    
    # Build the Drive service
    drive_service = build('drive', 'v3', credentials=credentials)
    
    # Get file metadata
    file_metadata = drive_service.files().get(fileId=file_id).execute()
    logger.info(f"Found file: {file_metadata.get('name')}")
    
    # Create temporary file to store the video
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    
    # Download the file content
    request = drive_service.files().get_media(fileId=file_id)
    
    with open(temp_file, 'wb') as f:
        # Stream the download to avoid memory issues with large files
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            logger.info(f"Download progress: {int(status.progress() * 100)}%")
    
    logger.info(f"Video downloaded to temporary file: {temp_file}")
    return temp_file

def upload_to_youtube(video_path, title, description, tags=None):
    """Upload a video to YouTube using stored OAuth credentials."""
    
    # Check if video file exists
    if not os.path.exists(video_path):
        logger.error(f"Error: Video file not found at {video_path}")
        return None
    
    try:
        # Get authenticated YouTube service
        youtube = get_authenticated_youtube_service()
        
        # Prepare video metadata
        if tags is None:
            tags = []
        
        # Add #Shorts tag for vertical videos
        if "#Shorts" not in tags:
            tags.append("#Shorts")
        
        # Set up the video metadata
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "22"  # People & Blogs category
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }
        
        # Create upload request
        media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
        
        # Execute the upload
        logger.info(f"Uploading video to YouTube: {title}")
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = request.execute()
        
        # Get the video ID
        video_id = response["id"]
        logger.info(f"Upload complete! YouTube Video ID: {video_id}")
        logger.info(f"YouTube URL: https://www.youtube.com/watch?v={video_id}")
        
        return video_id
        
    except Exception as e:
        logger.error(f"An error occurred during upload: {str(e)}")
        return None

def present_reels_for_selection(final_reels_dir: str) -> dict:
    """Present the final reels to the user and let them choose one for YouTube upload."""
    
    # Load all reel metadata files
    reel_files = []
    for filename in os.listdir(final_reels_dir):
        if filename.endswith('.json') and filename.startswith('final_'):
            file_path = os.path.join(final_reels_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reel_files.append({
                        'path': file_path,
                        'data': data
                    })
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    
    # Sort by index in filename
    reel_files.sort(key=lambda x: int(os.path.basename(x['path']).split('_')[1]))
    
    # Present reels to user
    print("\n===== AVAILABLE REELS FOR YOUTUBE UPLOAD =====")
    
    for i, reel in enumerate(reel_files, 1):
        data = reel['data']
        title = data.get('title', 'Untitled')
        score = data.get('viral_analysis', {}).get('score', 'N/A') 
        
        # Get first 100 characters of script for preview
        script_preview = data.get('heygen_script', '')[:100].replace('\n', ' ') + '...'
        
        print(f"{i}. {title}")
        print(f"   Score: {score}")
        print(f"   Preview: {script_preview}")
        print()
    
    # Get user selection
    while True:
        try:
            selection = int(input("Enter the number of the reel to upload to YouTube (1-10): "))
            if 1 <= selection <= len(reel_files):
                return reel_files[selection-1]['data']
            else:
                print(f"Please enter a number between 1 and {len(reel_files)}")
        except ValueError:
            print("Please enter a valid number")

def process_selected_reel(metadata):
    """Process the selected reel - generate HeyGen video and upload to YouTube."""
    
    # Step 1: Generate HeyGen video
    video_url = generate_heygen_video(metadata)
    if not video_url:
        logger.error("Failed to generate video with HeyGen. Workflow aborted.")
        return False
    
    # Step 2: Upload to Google Drive
    title = metadata.get('title', 'HeyGen Generated Video')
    file_name = f"{title.replace(' ', '_')[:30]}_video.mp4"  # Limit filename length
    drive_info = upload_to_drive(video_url, file_name, title)
    if not drive_info:
        logger.error("Failed to upload to Google Drive. Workflow aborted.")
        return False
    
    file_id = drive_info['file_id']
    temp_video_path = drive_info['temp_path']
    
    try:
        # Step 3: Download from Google Drive for YouTube upload
        temp_video_path = download_from_drive(file_id)
        
        # Step 4: Upload to YouTube
        description = metadata.get('description', '')
        tags = metadata.get('hashtags', [])
        
        video_id = upload_to_youtube(temp_video_path, title, description, tags)
        
        if video_id:
            logger.info("✅ YouTube upload successful!")
            logger.info(f"Video '{title}' is now available on YouTube: https://www.youtube.com/watch?v={video_id}")
            return True
        else:
            logger.error("❌ YouTube upload failed.")
            return False
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            logger.info(f"Removed temporary video file: {temp_video_path}")

def main():
    # Default edit prompt 
    default_edit_prompt = """Убрать: 
- Приветствие (добрый день, привет, и т.д.)
- Представления эксперта (я Сергей Черненко)
- Фразы типа «вот про это мы поговорим в следующем ролике»

Добавить:
- Начать с одного из вариантов цепляющего вступления:
  * «Это видео для тех, кто...» (например: хочет научиться монтировать, но не знает, с чего начать)
  * «Это история о том, как...» (например: я сделал вирусное видео, даже не зная, как монтировать)
  * «А вы знали, что...» (например: можно монтировать видео бесплатно на профессиональном уровне)
  * «Вряд ли вы мне поверите, но...» (например: раньше я боялся монтировать, потому что думал, что это сложно)
  * «У меня ушло несколько лет, чтобы...» (например: понять, как сделать видео, которые набирают миллионы просмотров)
  * Начать со слова «короче» - посыл "сейчас я быстро расскажу"
  * Использовать фразы с превосходными прилагательными: "Самый классный в мире...", "Самый провальный...", "Самый лучший...", "Самый быстрый...", "Самый неэффективный способ..."

Сохранить:
- Основное образовательное содержание
- Ключевые тезисы и рекомендации
- Призыв к действию в конце"""

    print("========== COMBINED WORKFLOW: GOOGLE DOC TO YOUTUBE ==========")
    print("This workflow will process a Google Doc, create reel scripts,")
    print("pick the best reels, and upload your selection to YouTube.")
    print("============================================================\n")
    
    # Get Google Doc URL
    doc_url = input("Enter the Google Doc URL: ").strip()
    
    # Create output directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"output_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Step 1: Process Google Doc
        analyzed_doc_path = process_google_doc(doc_url, SERVICE_ACCOUNT_PATH)
        
        # Step 2: Generate reel scripts
        metadata_dir = create_reel_scripts(
            input_file=analyzed_doc_path,
            output_dir=output_dir,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 3: Pick top reels
        top_reels_dir = pick_top_reels(
            metadata_dir=metadata_dir,
            top_n=10,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 4: Final reel editing
        final_reels_dir = final_reel_editing(
            top_reels_dir=top_reels_dir,
            edit_prompt=default_edit_prompt,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 5: Let user select a reel for YouTube
        print("\nAll reel scripts have been generated and edited.")
        proceed = input("Do you want to select a reel to upload to YouTube? (y/n): ").strip().lower()
        
        if proceed == 'y':
            # Present reels and get selection
            selected_reel = present_reels_for_selection(final_reels_dir)
            
            # Process selected reel
            success = process_selected_reel(selected_reel)
            
            if success:
                print("\n✅ Complete workflow finished successfully!")
                print(f"All processed reels are saved in: {final_reels_dir}")
            else:
                print("\n❌ YouTube upload failed. However, your processed reels are still available.")
                print(f"You can find them in: {final_reels_dir}")
        else:
            print("\nWorkflow completed without YouTube upload.")
            print(f"All processed reels are saved in: {final_reels_dir}")
    
    except Exception as e:
        logger.error(f"An error occurred in the workflow: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        print("Workflow aborted due to an error.")

if __name__ == "__main__":
    main() 