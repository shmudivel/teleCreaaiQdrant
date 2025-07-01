import os
import json
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload
import tempfile
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import io
import pickle
import random

# Disable OAuthlib's HTTPS verification for local development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Hardcoded OAuth credentials
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
TOKEN_FILE = "youtube_token.json"  # Change to JSON format

def download_from_drive(file_id):
    """Download video from Google Drive using service account authentication."""
    
    print(f"Downloading video from Google Drive (File ID: {file_id})...")
    
    # Use service account credentials
    credentials_path = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/bustling-folio-439811-h8-539f8ab05fa7.json"
    scopes = ['https://www.googleapis.com/auth/drive.readonly']
    credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
    
    # Build the Drive service
    drive_service = googleapiclient.discovery.build('drive', 'v3', credentials=credentials)
    
    # Get file metadata
    file_metadata = drive_service.files().get(fileId=file_id).execute()
    print(f"Found file: {file_metadata.get('name')}")
    
    # Create temporary file to store the video
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_file_path = temp_file.name
    temp_file.close()
    
    # Download the file content
    request = drive_service.files().get_media(fileId=file_id)
    
    with open(temp_file_path, 'wb') as f:
        # Stream the download to avoid memory issues with large files
        downloader = googleapiclient.http.MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download progress: {int(status.progress() * 100)}%")
    
    print(f"Video downloaded to temporary file: {temp_file_path}")
    return temp_file_path

def get_authenticated_service():
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
                print("Using stored credentials, no browser authentication needed")
        
        # If credentials don't exist or are invalid, we need to create new ones
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                print("Refreshing expired credentials...")
                credentials.refresh(Request())
            else:
                print("No valid credentials found. Need browser authentication (one-time setup)...")
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
                print(f"Credentials saved to {TOKEN_FILE} for future use")
        
        return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
    
    finally:
        # Clean up client secrets
        if os.path.exists(client_secrets_file):
            os.remove(client_secrets_file)

def upload_to_youtube(video_path, title, description, tags=None):
    """Upload a video to YouTube using stored OAuth credentials."""
    
    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return None
    
    try:
        # Get authenticated YouTube service
        youtube = get_authenticated_service()
        
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
        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
        
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
        print(f"Upload complete! Video ID: {video_id}")
        print(f"Video URL: https://www.youtube.com/watch?v={video_id}")
        
        return video_id
        
    except Exception as e:
        print(f"An error occurred during upload: {str(e)}")
        return None

def extract_file_id_from_url(drive_url):
    """Extract the file ID from a Google Drive URL."""
    # Handle various Drive URL formats
    if '/file/d/' in drive_url:
        # Format: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
        start_index = drive_url.find('/file/d/') + 8
        end_index = drive_url.find('/', start_index)
        if end_index == -1:
            end_index = len(drive_url)
        return drive_url[start_index:end_index]
    
    # Handle direct ID
    if len(drive_url) >= 25 and '/' not in drive_url and '.' not in drive_url:
        return drive_url
    
    print(f"Could not extract file ID from: {drive_url}")
    return None

def main():
    try:
        # Ask for Google Drive URL or file ID
        drive_link = input("Enter the Google Drive video URL or file ID: ")
        
        # Extract file ID from URL if needed
        file_id = extract_file_id_from_url(drive_link)
        if not file_id:
            print("Invalid Google Drive URL or file ID")
            return
        
        # Download the video from Google Drive
        temp_video_path = download_from_drive(file_id)
        
        # Load the metadata JSON file
        json_path = input("Enter path to the JSON metadata file (or press Enter to use default): ")
        if not json_path:
            json_path = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/tests/big_text_to_reels/final_output/final_reels/final_07_reel_7.json"
        
        with open(json_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Extract metadata
        title = metadata.get('title', 'HeyGen Generated Video')
        description = metadata.get('description', '')
        
        # Use hashtags as tags
        tags = metadata.get('hashtags', [])
        
        # Upload the video
        try:
            video_id = upload_to_youtube(temp_video_path, title, description, tags)
            
            if video_id:
                print("Video upload completed successfully.")
            else:
                print("Video upload failed.")
        finally:
            # Clean up temporary file
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
                print(f"Removed temporary video file: {temp_video_path}")
                
    except Exception as e:
        print(f"An error occurred in main: {str(e)}")
        print("Video upload failed.")

if __name__ == "__main__":
    main() 