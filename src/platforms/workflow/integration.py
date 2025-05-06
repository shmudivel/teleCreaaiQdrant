import os
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

# Import modules from local files
from .analyze_google_doc import extract_doc_id_from_url, get_document_content, analyze_with_claude
from .create_reel_scripts import ReelGenerator
from .reel_picker import load_metadata_files, analyze_viral_potential, select_top_reels, save_top_reels, get_client
# Import prompts
from .prompts import (
    DEFAULT_EDIT_GUIDELINES, HOOK_VARIATIONS, CALL_TO_ACTION_VARIATIONS,
    FINAL_EDITING_PROMPT, FINAL_EDITING_SYSTEM_PROMPT,
    HEYGEN_OPTIMIZATION_PROMPT, HEYGEN_OPTIMIZATION_SYSTEM_PROMPT,
    SCRIPT_VALIDATION_PROMPT, SCRIPT_VALIDATION_SYSTEM_PROMPT,
    NUMBER_CONVERSION_PROMPT, NUMBER_CONVERSION_SYSTEM_PROMPT
)
# Import API utilities
from .api_utils import call_claude_api, RateLimiter, exponential_backoff_retry, create_claude_client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for API keys and paths
SERVICE_ACCOUNT_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_PATH", "./bustling-folio-439811-h8-539f8ab05fa7.json")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
HEYGEN_API_KEY = os.environ.get("HEYGEN_API_KEY", "NzYzODNmNTI5ODYyNGMyYTg1NzFhNTNmOWY4M2Q4OTYtMTc0MDczMjczOQ==")
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "REMOVED_GOOGLE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "REMOVED_GOOGLE_CLIENT_SECRET")
TOKEN_FILE = "youtube_token.json"

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

def pick_top_reels(metadata_dir: str, top_n: int = 7, api_key: Optional[str] = None) -> str:
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

@exponential_backoff_retry()
def edit_reel_script(client, reel_data, edit_prompt, hook_variant, call_to_action_variant, model="claude-3-7-sonnet-20250219"):
    """Edit a reel script with retry logic."""
    script = reel_data.get('heygen_script', '')
    title = reel_data.get('title', '')
    
    # Format the prompt
    user_prompt = FINAL_EDITING_PROMPT.format(
        script=script,
        title=title,
        edit_prompt=edit_prompt,
        hook_variant=hook_variant,
        call_to_action_variant=call_to_action_variant
    )
    
    result = call_claude_api(
        client=client,
        model=model,
        prompt=user_prompt,
        system=FINAL_EDITING_SYSTEM_PROMPT,
        max_tokens=1500,
        temperature=0.7
    )
    
    return result.strip()

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
    client = create_claude_client(api_key)
    
    # Define output directory
    parent_dir = os.path.dirname(top_reels_dir)
    final_reels_dir = os.path.join(parent_dir, "final_reels")
    
    # Create output directory path
    Path(final_reels_dir).mkdir(parents=True, exist_ok=True)
    
    # Create rate limiter to avoid hitting API limits
    rate_limiter = RateLimiter(calls_per_minute=10)
    
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
        hook_variant = random.choice(HOOK_VARIATIONS)
        
        # Select a random call to action variant
        call_to_action_variant = random.choice(CALL_TO_ACTION_VARIATIONS)
        
        try:
            # Use rate limiter to prevent hitting API limits
            with rate_limiter:
                # Call Claude to edit the script
                logger.info(f"Editing reel {i+1}/{len(metadata_files)}...")
                edited_script = edit_reel_script(client, reel_data, edit_prompt, hook_variant, call_to_action_variant)
            
            # Update the reel data
            reel_data['original_script'] = reel_data.get('heygen_script', '')
            reel_data['heygen_script'] = edited_script
            reel_data['hook_variant'] = hook_variant
            reel_data['call_to_action_variant'] = call_to_action_variant
            
            # Save the edited reel metadata
            output_path = os.path.join(final_reels_dir, f"final_{i+1:02d}_{os.path.basename(reel_data.get('filename', f'reel_{i+1}.json'))}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(reel_data, f, ensure_ascii=False, indent=2)
            
            # Also save as a plain text file for heygen
            title = reel_data.get('title', '')
            heygen_filename = f"final_heygen_{i+1:02d}.txt"
            heygen_path = os.path.join(final_reels_dir, heygen_filename)
            with open(heygen_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n{edited_script}")
            
            logger.info(f"Saved edited reel to {output_path}")
            
        except Exception as e:
            logger.error(f"Error editing reel {i+1}: {str(e)}")
    
    logger.info(f"Final reel editing completed. Edited reels saved to: {final_reels_dir}")
    return final_reels_dir

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
    
    # Allow custom token file path via environment variable
    token_file_path = os.environ.get("YOUTUBE_TOKEN_PATH", TOKEN_FILE)
    
    # Also check in common locations
    potential_token_paths = [
        token_file_path,
        TOKEN_FILE,
        "./youtube_token.json",
        "/app/youtube_token.json",  # Docker container path
        os.path.join(os.path.dirname(__file__), "youtube_token.json"),
        "/app/tests/big_text_to_reels/youtube_token.json",  # Specific path mentioned by user
        "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/tests/big_text_to_reels/youtube_token.json"
    ]
    
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
        # Try all potential token file paths
        for token_path in potential_token_paths:
            if os.path.exists(token_path):
                logger.info(f"Found YouTube token file at: {token_path}")
                try:
                    with open(token_path, 'r') as token_file:
                        token_data = json.load(token_file)
                        credentials = Credentials.from_authorized_user_info(token_data)
                        logger.info("Using stored YouTube credentials, no browser authentication needed")
                        break
                except Exception as e:
                    logger.warning(f"Error loading token from {token_path}: {str(e)}")
        
        # If credentials don't exist or are invalid, we need to create new ones
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                logger.info("Refreshing expired credentials...")
                try:
                    credentials.refresh(Request())
                    # Save refreshed credentials to file
                    token_data = {
                        'token': credentials.token,
                        'refresh_token': credentials.refresh_token,
                        'token_uri': credentials.token_uri,
                        'client_id': credentials.client_id,
                        'client_secret': credentials.client_secret,
                        'scopes': credentials.scopes
                    }
                    with open(token_file_path, 'w') as token_file:
                        json.dump(token_data, token_file)
                    logger.info(f"Refreshed YouTube credentials saved to {token_file_path}")
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {str(e)}")
                    raise
            else:
                # In a headless environment, we can't run a browser so provide a clear error
                # and alternative instructions
                try:
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
                    
                    with open(token_file_path, 'w') as token_file:
                        json.dump(token_data, token_file)
                    logger.info(f"YouTube credentials saved to {token_file_path} for future use")
                except Exception as e:
                    # Provide helpful instructions for headless environments
                    logger.error(f"Browser authentication not available: {str(e)}")
                    logger.error("To fix this issue:")
                    logger.error("1. Run the YouTube authentication on a local machine with a browser")
                    logger.error("2. Copy the resulting youtube_token.json file to the Docker container or application directory")
                    logger.error("3. Set YOUTUBE_TOKEN_PATH environment variable if needed")
                    
                    # Re-raise the exception
                    raise RuntimeError("YouTube OAuth authentication requires a browser. Please pre-authenticate and provide a token file.") from e
        
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

def process_selected_reel(metadata):
    """Process the selected reel - generate HeyGen video and upload to YouTube."""
    
    # Ensure we're using the final script with all optimizations applied
    if 'pre_conversion_script' in metadata:
        logger.info("Using converted script with numbers as words for optimal HeyGen delivery")
    elif 'pre_validation_script' in metadata:
        logger.warning("Using validated script but without number conversion - consider adding number conversion step")
    elif 'original_script' in metadata:
        logger.warning("Using only optimized script without validation or number conversion - consider adding these steps")
    
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
        
        try:
            logger.info(f"Attempting to upload video to YouTube: {title}")
            video_id = upload_to_youtube(temp_video_path, title, description, tags)
            
            if video_id:
                logger.info("✅ YouTube upload successful!")
                logger.info(f"Video '{title}' is now available on YouTube: https://www.youtube.com/watch?v={video_id}")
                return True
            else:
                logger.error("❌ YouTube upload failed. Check logs for details.")
                return False
        except RuntimeError as e:
            # Handle the specific error about browser authentication
            if "OAuth authentication requires a browser" in str(e):
                logger.error("❌ YouTube upload failed: Authentication error")
                logger.error("To fix this issue:")
                logger.error("1. Run the YouTube authentication on a local machine with a browser")
                logger.error("2. Copy the resulting youtube_token.json file to one of these locations:")
                logger.error("   - /app/youtube_token.json (Docker container)")
                logger.error("   - The application root directory")
                logger.error("   - Set YOUTUBE_TOKEN_PATH environment variable")
                logger.error(f"Detailed error: {str(e)}")
                return False
            else:
                # Re-raise other runtime errors
                raise
        except Exception as e:
            logger.error(f"❌ YouTube upload failed: {str(e)}")
            return False
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            logger.info(f"Removed temporary video file: {temp_video_path}")

@exponential_backoff_retry()
def optimize_heygen_script(client, script, model="claude-3-7-sonnet-20250219"):
    """Optimize a script for natural delivery by HeyGen avatar, with retry logic.
    
    Args:
        client: Anthropic client
        script: The script to optimize
        model: Claude model to use
        
    Returns:
        Optimized script with SSML tags and improved pacing
    """
    # Format the prompt
    user_prompt = HEYGEN_OPTIMIZATION_PROMPT.format(script=script)
    
    result = call_claude_api(
        client=client,
        model=model,
        prompt=user_prompt,
        system=HEYGEN_OPTIMIZATION_SYSTEM_PROMPT,
        max_tokens=2000,
        temperature=0.4
    )
    
    return result.strip()

def optimize_heygen_scripts(final_reels_dir: str, api_key: Optional[str] = None) -> str:
    """Optimize scripts for natural delivery by HeyGen avatar.
    
    Args:
        final_reels_dir: Directory containing edited reel scripts
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the directory with optimized scripts
    """
    logger.info("Step 5: HeyGen script optimization")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Get Anthropic client
    client = create_claude_client(api_key)
    
    # Define output directory
    parent_dir = os.path.dirname(final_reels_dir)
    optimized_dir = os.path.join(parent_dir, "optimized_scripts")
    
    # Create output directory path
    Path(optimized_dir).mkdir(parents=True, exist_ok=True)
    
    # Create rate limiter to avoid hitting API limits
    rate_limiter = RateLimiter(calls_per_minute=10)
    
    # Load reel data
    logger.info(f"Loading final reels from {final_reels_dir}...")
    reels_data = []
    for filename in os.listdir(final_reels_dir):
        if filename.endswith('.json') and filename.startswith('final_'):
            file_path = os.path.join(final_reels_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reels_data.append({
                        'data': data,
                        'filename': filename
                    })
                    logger.info(f"Loaded {filename}")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    
    for i, reel_item in enumerate(reels_data):
        reel_data = reel_item['data']
        script = reel_data.get('heygen_script', '')
        title = reel_data.get('title', '')
        
        try:
            # Use rate limiter to prevent hitting API limits
            with rate_limiter:
                # Optimize script for HeyGen
                logger.info(f"Optimizing script {i+1}/{len(reels_data)} for HeyGen...")
                optimized_script = optimize_heygen_script(client, script)
            
            # Create a clean output with only necessary fields
            optimized_data = {
                'heygen_script': optimized_script,
                'title': title
            }
            
            # Copy other essential fields except scripts
            for key in ['hashtags', 'description']:
                if key in reel_data:
                    optimized_data[key] = reel_data[key]
            
            # Save the optimized reel metadata
            output_path = os.path.join(optimized_dir, f"optimized_{os.path.basename(reel_item['filename'])}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(optimized_data, f, ensure_ascii=False, indent=2)
            
            # Also save as a plain text file for HeyGen
            heygen_filename = f"optimized_heygen_{i+1:02d}.txt"
            heygen_path = os.path.join(optimized_dir, heygen_filename)
            with open(heygen_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n{optimized_script}")
            
            logger.info(f"Saved optimized script to {output_path}")
            
        except Exception as e:
            logger.error(f"Error optimizing script {i+1}: {str(e)}")
    
    logger.info(f"Script optimization completed. Optimized scripts saved to: {optimized_dir}")
    return optimized_dir

@exponential_backoff_retry()
def validate_heygen_script(client, script_data, model="claude-3-7-sonnet-20250219"):
    """Validate and fix a HeyGen script if it doesn't comply with rules.
    
    Args:
        client: Anthropic client
        script_data: Dictionary containing script data ('heygen_script', 'title')
        model: Claude model to use
        
    Returns:
        Fixed script that complies with HeyGen rules
    """
    script = script_data.get('heygen_script', '')
    title = script_data.get('title', '')
    
    # Format the prompt with top 10 hook examples
    hook_examples = "\n".join(HOOK_VARIATIONS[:10])
    user_prompt = SCRIPT_VALIDATION_PROMPT.format(
        hook_examples=hook_examples,
        title=title,
        script=script
    )
    
    result = call_claude_api(
        client=client,
        model=model,
        prompt=user_prompt,
        system=SCRIPT_VALIDATION_SYSTEM_PROMPT,
        max_tokens=2000,
        temperature=0.3
    )
    
    return result.strip()

def validate_heygen_scripts(optimized_dir: str, api_key: Optional[str] = None) -> str:
    """Validate and fix optimized scripts to ensure they comply with HeyGen rules.
    
    Args:
        optimized_dir: Directory containing optimized scripts
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the directory with validated scripts
    """
    logger.info("Step 6: HeyGen script validation and fixing")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Get Anthropic client
    client = create_claude_client(api_key)
    
    # Define output directory
    parent_dir = os.path.dirname(optimized_dir)
    validated_dir = os.path.join(parent_dir, "validated_scripts")
    
    # Create output directory path
    Path(validated_dir).mkdir(parents=True, exist_ok=True)
    
    # Create rate limiter to avoid hitting API limits
    rate_limiter = RateLimiter(calls_per_minute=10)
    
    # Load optimized reel data
    logger.info(f"Loading optimized scripts from {optimized_dir}...")
    reels_data = []
    for filename in os.listdir(optimized_dir):
        if filename.endswith('.json') and filename.startswith('optimized_'):
            file_path = os.path.join(optimized_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reels_data.append({
                        'data': data,
                        'filename': filename
                    })
                    logger.info(f"Loaded {filename}")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    
    for i, reel_item in enumerate(reels_data):
        reel_data = reel_item['data']
        
        try:
            # Use rate limiter to prevent hitting API limits
            with rate_limiter:
                # Validate and fix the script
                logger.info(f"Validating script {i+1}/{len(reels_data)}...")
                validated_script = validate_heygen_script(client, reel_data)
            
            # Create output data
            validated_data = reel_data.copy()
            
            # Save original script before validation
            validated_data['pre_validation_script'] = reel_data.get('heygen_script', '')
            
            # Update with validated script
            validated_data['heygen_script'] = validated_script
            
            # Save the validated data
            output_path = os.path.join(validated_dir, f"validated_{os.path.basename(reel_item['filename']).replace('optimized_', '')}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(validated_data, f, ensure_ascii=False, indent=2)
            
            # Also save as plain text for easy use with HeyGen
            title = reel_data.get('title', '')
            heygen_filename = f"validated_heygen_{i+1:02d}.txt"
            heygen_path = os.path.join(validated_dir, heygen_filename)
            with open(heygen_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n{validated_script}")
            
            logger.info(f"Saved validated script to {output_path}")
            
        except Exception as e:
            logger.error(f"Error validating script {i+1}: {str(e)}")
    
    logger.info(f"Script validation completed. Validated scripts saved to: {validated_dir}")
    return validated_dir

@exponential_backoff_retry()
def convert_numbers_to_words(client, script_data, model="claude-3-7-sonnet-20250219"):
    """Convert all numbers in a script to their word representation in Russian.
    
    Args:
        client: Anthropic client
        script_data: Dictionary containing script data ('heygen_script', 'title')
        model: Claude model to use
        
    Returns:
        Script with all numbers converted to words
    """
    script = script_data.get('heygen_script', '')
    
    # Format the prompt with the script
    user_prompt = NUMBER_CONVERSION_PROMPT.format(script=script)
    
    result = call_claude_api(
        client=client,
        model=model,
        prompt=user_prompt,
        system=NUMBER_CONVERSION_SYSTEM_PROMPT,
        max_tokens=2000,
        temperature=0.3
    )
    
    return result.strip()

def convert_all_numbers_to_words(validated_dir: str, api_key: Optional[str] = None) -> str:
    """Convert all numbers to words in validated scripts.
    
    Args:
        validated_dir: Directory containing validated scripts
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the directory with number-converted scripts
    """
    logger.info("Step 7: Converting numbers to words in scripts")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Get Anthropic client
    client = create_claude_client(api_key)
    
    # Define output directory
    parent_dir = os.path.dirname(validated_dir)
    converted_dir = os.path.join(parent_dir, "converted_scripts")
    
    # Create output directory path
    Path(converted_dir).mkdir(parents=True, exist_ok=True)
    
    # Create rate limiter to avoid hitting API limits
    rate_limiter = RateLimiter(calls_per_minute=10)
    
    # Load validated reel data
    logger.info(f"Loading validated scripts from {validated_dir}...")
    reels_data = []
    for filename in os.listdir(validated_dir):
        if filename.endswith('.json') and filename.startswith('validated_'):
            file_path = os.path.join(validated_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reels_data.append({
                        'data': data,
                        'filename': filename
                    })
                    logger.info(f"Loaded {filename}")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    
    for i, reel_item in enumerate(reels_data):
        reel_data = reel_item['data']
        
        try:
            # Use rate limiter to prevent hitting API limits
            with rate_limiter:
                # Convert numbers to words
                logger.info(f"Converting numbers in script {i+1}/{len(reels_data)}...")
                converted_script = convert_numbers_to_words(client, reel_data)
            
            # Create output data
            converted_data = reel_data.copy()
            
            # Save pre-conversion script
            converted_data['pre_conversion_script'] = reel_data.get('heygen_script', '')
            
            # Update with converted script
            converted_data['heygen_script'] = converted_script
            
            # Save the converted data
            output_path = os.path.join(converted_dir, f"converted_{os.path.basename(reel_item['filename']).replace('validated_', '')}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(converted_data, f, ensure_ascii=False, indent=2)
            
            # Also save as plain text for easy use with HeyGen
            title = reel_data.get('title', '')
            heygen_filename = f"converted_heygen_{i+1:02d}.txt"
            heygen_path = os.path.join(converted_dir, heygen_filename)
            with open(heygen_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n{converted_script}")
            
            logger.info(f"Saved converted script to {output_path}")
            
        except Exception as e:
            logger.error(f"Error converting numbers in script {i+1}: {str(e)}")
    
    logger.info(f"Number conversion completed. Converted scripts saved to: {converted_dir}")
    return converted_dir

def process_google_doc_to_reels(doc_url: str, output_dir: Optional[str] = None, top_n: int = 7) -> Dict[str, str]:
    """Process a Google Doc and convert it to reels.
    
    This is the main function that combines all the steps of the workflow.
    
    Args:
        doc_url: URL of the Google Doc to process
        output_dir: Directory to save output files (optional)
        top_n: Number of top reels to select (default: 7)
        
    Returns:
        Dictionary with paths to generated content
    """
    # Use edit guidelines from prompts.py
    edit_prompt = DEFAULT_EDIT_GUIDELINES
    
    # Create output directory if not provided
    if not output_dir:
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
            top_n=top_n,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 4: Final reel editing
        final_reels_dir = final_reel_editing(
            top_reels_dir=top_reels_dir,
            edit_prompt=edit_prompt,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 5: Optimize scripts for HeyGen
        optimized_dir = optimize_heygen_scripts(
            final_reels_dir=final_reels_dir,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 6: Validate and fix scripts
        validated_dir = validate_heygen_scripts(
            optimized_dir=optimized_dir,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 7: Convert numbers to words
        converted_dir = convert_all_numbers_to_words(
            validated_dir=validated_dir,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Return paths to various directories for reference
        return {
            "analyzed_doc": analyzed_doc_path,
            "metadata_dir": metadata_dir,
            "top_reels_dir": top_reels_dir,
            "final_reels_dir": final_reels_dir,
            "optimized_dir": optimized_dir,
            "validated_dir": validated_dir,
            "converted_dir": converted_dir
        }
    
    except Exception as e:
        logger.error(f"An error occurred in the workflow: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise 