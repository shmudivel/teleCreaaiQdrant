import requests
import json
import time
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2 import service_account
import io

# Load the metadata JSON file
with open('/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/tests/big_text_to_reels/final_output/final_reels/final_07_reel_7.json', 'r', encoding='utf-8') as f:
    metadata = json.load(f)
    
# Extract the reel script from the metadata
reel_script = metadata["heygen_script"]

# Your HeyGen API key - replace with your actual API key
API_KEY = "NzYzODNmNTI5ODYyNGMyYTg1NzFhNTNmOWY4M2Q4OTYtMTc0MDczMjczOQ=="
headers = {
    "X-Api-Key": API_KEY,
    "Content-Type": "application/json"
}

# Extract the script from metadata
script = metadata["heygen_script"]
title = metadata["title"]

# You can customize these values based on your preferences
# For avatar_id and voice_id, you'd need to use your own created or HeyGen's available options
avatar_id = "866d2e167e8a43a38dcb4ddf96a52d97"  # Replace with your avatar ID
voice_id = "aa6539b580bf4c9a93879977044e9a12"    # Replace with your voice ID

# API endpoint for video generation
generate_url = "https://api.heygen.com/v2/video/generate"

# Prepare the request payload
payload = {
    "video_inputs": [
        {
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id,
                "avatar_style": "normal",  # Can be "normal" or other styles supported by HeyGen
                "scale": 2.2,  # Increased scale for closer zoom
                "position": {
                    "x": 0,    # Center horizontally
                    "y": -0.3  # Move the avatar up slightly more in the frame
                }
            },
            "voice": {
                "type": "text",
                "input_text": script,
                "voice_id": voice_id
            },
            "background": {
                "type": "color",
                "value": "#000000"  # Black background for better vertical video appearance
            }
        }
    ],
    "dimension": {
        "width": 720,  # Standard portrait video dimensions for reels/shorts
        "height": 1280
    },
    "video_type": "vertical",  # Explicitly set vertical format
    "caption": True,  # Enable captions
    "title": title
}

def generate_video():
    # Generate the video
    print(f"Generating video for: {title}")
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
    return video_id

def check_video_status(video_id):
    # Check video generation status
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
            time.sleep(10)  # Wait for 10 seconds before checking again
        
        elif status == "failed":
            error = status_data["data"].get("error", "Unknown error")
            print(f"Video generation failed: {error}")
            return None
        
        else:
            print(f"Unknown status: {status}")
            return None

def authenticate_google_drive():
    """Authenticate with Google Drive API using service account credentials."""
    credentials_path = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/bustling-folio-439811-h8-539f8ab05fa7.json"
    
    # Authenticate using service account
    scopes = ['https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
    drive_service = build('drive', 'v3', credentials=credentials)
    return drive_service

def upload_to_drive(video_url, file_name):
    """Upload the video to Google Drive."""
    print(f"Uploading video to Google Drive...")
    
    # Create a temporary file to store the downloaded video
    temp_file = f'/tmp/{file_name}'
    
    # Download the video from the URL
    response = requests.get(video_url)
    if response.status_code != 200:
        print(f"Error downloading video from URL: {response.status_code}")
        return False
    
    # Save temporarily
    with open(temp_file, "wb") as f:
        f.write(response.content)
    
    # Authenticate with Google Drive
    drive_service = authenticate_google_drive()
    
    # Upload to Google Drive
    file_metadata = {
        'name': file_name,
        'description': title,
        'mimeType': 'video/mp4'
    }
    
    media = MediaFileUpload(temp_file, mimetype='video/mp4', resumable=True)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id,webViewLink').execute()
    
    # Clean up temporary file
    os.remove(temp_file)
    
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
    
    return file_id

def main():
    # Generate the video
    video_id = generate_video()
    if not video_id:
        return
    
    # Check the video status and get the URL when complete
    video_url = check_video_status(video_id)
    if not video_url:
        return
    
    # Upload the video to Google Drive
    file_name = f"reel_7_generated_video.mp4"
    upload_to_drive(video_url, file_name)

if __name__ == "__main__":
    main() 