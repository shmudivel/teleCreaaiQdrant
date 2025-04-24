import requests
import json
import time
import os
import tempfile
import random
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import google_auth_oauthlib.flow
import io

# YouTube OAuth credentials
YOUTUBE_CLIENT_ID = "REMOVED_GOOGLE_CLIENT_ID"
YOUTUBE_CLIENT_SECRET = "REMOVED_GOOGLE_CLIENT_SECRET"
TOKEN_FILE = "youtube_token.json"

# Disable OAuthlib's HTTPS verification for local development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

def load_metadata(json_path):
    """Load metadata from JSON file"""
    print(f"Loading metadata from: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Validate required fields
    required_fields = ["heygen_script", "title"]
    for field in required_fields:
        if field not in metadata:
            raise ValueError(f"Required field '{field}' not found in JSON metadata")
    
    return metadata

def generate_heygen_video(metadata):
    """Generate a video using HeyGen API"""
    # Extract data from metadata
    script = metadata["heygen_script"]
    title = metadata["title"]
    
    # Your HeyGen API key
    API_KEY = "NzYzODNmNTI5ODYyNGMyYTg1NzFhNTNmOWY4M2Q4OTYtMTc0MDczMjczOQ=="
    headers = {
        "X-Api-Key": API_KEY,
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
    print(f"Generating HeyGen video for: {title}")
    response = requests.post(generate_url, json=payload, headers=headers)
    
    if response.status_code != 200:
        print(f"Error generating video: {response.text}")
        return None
    
    # Extract video ID from response
    response_data = response.json()
    if "data" not in response_data or "video_id" not in response_data["data"]:
        print(f"Error: Invalid response format: {response_data}")
        return None
    
    video_id = response_data["data"]["video_id"]
    print(f"Video generation started. Video ID: {video_id}")
    
    # Wait for video to complete
    video_url = check_heygen_video_status(video_id, headers)
    return video_url

def check_heygen_video_status(video_id, headers):
    """Check HeyGen video generation status"""
    video_status_url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    
    while True:
        response = requests.get(video_status_url, headers=headers)
        if response.status_code != 200:
            print(f"Error checking video status: {response.text}")
            return None
        
        status_data = response.json()
        if "data" not in status_data:
            print(f"Error: Invalid status response format: {status_data}")
            return None
        
        status = status_data["data"]["status"]
        
        if status == "completed":
            video_url = status_data["data"]["video_url"]
            thumbnail_url = status_data["data"]["thumbnail_url"]
            print(f"Video generation completed!")
            print(f"Video URL: {video_url}")
            print(f"Thumbnail URL: {thumbnail_url}")
            return video_url
        
        elif status == "processing" or status == "pending" or status == "waiting":
            print("Video is still processing. Checking status again in 10 seconds...")
            time.sleep(10)
        
        elif status == "failed":
            error = status_data["data"].get("error", "Unknown error")
            print(f"Video generation failed: {error}")
            return None
        
        else:
            print(f"Unknown status: {status}")
            return None

def upload_to_drive(video_url, file_name, title):
    """Upload the video to Google Drive."""
    print(f"Uploading video to Google Drive...")
    
    # Create a temporary file to store the downloaded video
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    
    # Download the video from the URL
    response = requests.get(video_url)
    if response.status_code != 200:
        print(f"Error downloading video from URL: {response.status_code}")
        return None
    
    # Save temporarily
    with open(temp_file, "wb") as f:
        f.write(response.content)
    
    print(f"Video downloaded to temporary file: {temp_file}")
    
    # Authenticate with Google Drive
    credentials_path = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/bustling-folio-439811-h8-539f8ab05fa7.json"
    scopes = ['https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
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
    
    print(f"Video uploaded successfully to Google Drive!")
    print(f"File ID: {file_id}")
    print(f"Web link: {web_link}")
    
    # Set permissions to anyone with the link can view
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    drive_service.permissions().create(fileId=file_id, body=permission).execute()
    print("Set permissions: Anyone with the link can view")
    
    # Clean up temporary file
    os.remove(temp_file)
    
    return {'file_id': file_id, 'temp_path': temp_file}

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
                print("Using stored YouTube credentials, no browser authentication needed")
        
        # If credentials don't exist or are invalid, we need to create new ones
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                print("Refreshing expired credentials...")
                credentials.refresh(Request())
            else:
                print("No valid YouTube credentials found. Need browser authentication (one-time setup)...")
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
                print(f"YouTube credentials saved to {TOKEN_FILE} for future use")
        
        return build("youtube", "v3", credentials=credentials)
    
    finally:
        # Clean up client secrets
        if os.path.exists(client_secrets_file):
            os.remove(client_secrets_file)

def download_from_drive(file_id):
    """Download video from Google Drive using service account authentication."""
    print(f"Downloading video from Google Drive (File ID: {file_id})...")
    
    # Use service account credentials
    credentials_path = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/bustling-folio-439811-h8-539f8ab05fa7.json"
    scopes = ['https://www.googleapis.com/auth/drive.readonly']
    credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
    
    # Build the Drive service
    drive_service = build('drive', 'v3', credentials=credentials)
    
    # Get file metadata
    file_metadata = drive_service.files().get(fileId=file_id).execute()
    print(f"Found file: {file_metadata.get('name')}")
    
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
            print(f"Download progress: {int(status.progress() * 100)}%")
    
    print(f"Video downloaded to temporary file: {temp_file}")
    return temp_file

def upload_to_youtube(video_path, title, description, tags=None):
    """Upload a video to YouTube using stored OAuth credentials."""
    
    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
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
        print(f"Uploading video to YouTube: {title}")
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = request.execute()
        
        # Get the video ID
        video_id = response["id"]
        print(f"Upload complete! YouTube Video ID: {video_id}")
        print(f"YouTube URL: https://www.youtube.com/watch?v={video_id}")
        
        return video_id
        
    except Exception as e:
        print(f"An error occurred during upload: {str(e)}")
        return None

def main():
    try:
        # Step 1: Ask for the JSON metadata file
        json_path = input("Enter path to the JSON metadata file (or press Enter to use default): ")
        if not json_path:
            json_path = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/tests/big_text_to_reels/final_output/final_reels/final_07_reel_7.json"
        
        # Step 2: Load metadata
        metadata = load_metadata(json_path)
        title = metadata.get('title', 'HeyGen Generated Video')
        description = metadata.get('description', '')
        tags = metadata.get('hashtags', [])
        
        # Step 3: Generate HeyGen video
        video_url = generate_heygen_video(metadata)
        if not video_url:
            print("Failed to generate video with HeyGen. Workflow aborted.")
            return
        
        # Step 4: Upload to Google Drive
        file_name = f"{title.replace(' ', '_')[:30]}_video.mp4"  # Limit filename length
        drive_info = upload_to_drive(video_url, file_name, title)
        if not drive_info:
            print("Failed to upload to Google Drive. Workflow aborted.")
            return
        
        file_id = drive_info['file_id']
        
        # Step 5: Download from Google Drive for YouTube upload
        temp_video_path = download_from_drive(file_id)
        
        # Step 6: Upload to YouTube
        try:
            video_id = upload_to_youtube(temp_video_path, title, description, tags)
            
            if video_id:
                print("✅ Complete workflow successful!")
                print(f"Video '{title}' is now available on YouTube: https://www.youtube.com/watch?v={video_id}")
            else:
                print("❌ YouTube upload failed.")
        finally:
            # Clean up temporary file
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
                print(f"Removed temporary video file: {temp_video_path}")
                
    except Exception as e:
        print(f"An error occurred in the workflow: {str(e)}")
        print("Workflow aborted.")

if __name__ == "__main__":
    main() 