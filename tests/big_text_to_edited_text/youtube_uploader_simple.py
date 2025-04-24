import os
import json
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload

# Disable OAuthlib's HTTPS verification for local development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

def upload_to_youtube(video_path, title, description, tags=None):
    """Upload a video to YouTube using OAuth 2.0 authentication."""
    
    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return None
    
    # Create client_secrets.json from environment variables
    client_id = input("Enter your OAuth client ID: ")
    client_secret = input("Enter your OAuth client secret: ")
    
    client_config = {
        "installed": {
            "client_id": client_id,
            "project_id": "youtube-uploader",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost"]
        }
    }
    
    client_secrets_file = "client_secrets.json"
    with open(client_secrets_file, "w") as f:
        json.dump(client_config, f)
    
    print(f"Created temporary {client_secrets_file} file")
    
    try:
        # Define the scopes
        scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        
        # Create a flow using the client secrets file
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        
        # Run the OAuth flow - this will open a browser window for authentication
        print("\nA browser window will open to authorize this application...")
        print("After authentication, you will be redirected to localhost.")
        credentials = flow.run_local_server(port=8082)
        
        # Build the YouTube API client
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
        
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
        print(f"Uploading video: {title}")
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
        print(f"An error occurred: {str(e)}")
        return None
    finally:
        # Clean up the temporary client secrets file
        try:
            os.remove(client_secrets_file)
            print(f"Removed temporary {client_secrets_file} file")
        except:
            pass

def main():
    try:
        # Path to the generated video
        video_path = '/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/output/generated_video.mp4'
        
        # Load metadata from the JSON file
        metadata_path = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/tests/big_text_to_reels/metadata/metadata_10.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Extract title and description
        title = metadata.get('section_title', 'ИИ в решении конфликтов')
        description = metadata.get('description', '')
        
        # Get hashtags
        hashtags = metadata.get('hashtags', [])
        
        # Upload the video
        video_id = upload_to_youtube(video_path, title, description, hashtags)
        
        if video_id:
            print("Video upload completed successfully.")
        else:
            print("Video upload failed.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Video upload failed.")

if __name__ == "__main__":
    main() 