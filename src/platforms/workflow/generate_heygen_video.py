import requests
import json
import base64
import os
import time

def upload_audio_file(api_key, audio_path):
    """Upload an audio file to HeyGen and get the asset ID."""
    url = "https://upload.heygen.com/v1/asset"
    
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "audio/mpeg"
    }
    
    print(f"Uploading audio file: {audio_path}")
    with open(audio_path, "rb") as audio_file:
        response = requests.post(url, headers=headers, data=audio_file)
    
    if response.status_code == 200:
        result = response.json()
        if "data" in result and "id" in result["data"]:
            asset_id = result["data"]["id"]
            print(f"Audio uploaded successfully. Asset ID: {asset_id}")
            return asset_id
        else:
            print(f"Error: Invalid response format: {result}")
            return None
    else:
        print(f"Error uploading audio: {response.status_code} - {response.text}")
        return None

def generate_video_with_multiple_avatars(api_key, avatar_ids, audio_asset_ids):
    url = "https://api.heygen.com/v2/video/generate"
    
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Build video_inputs array
    video_inputs = []
    for i in range(len(audio_asset_ids)):
        input = {
            "character": {
                "type": "avatar",
                "avatar_id": avatar_ids[i],
                "avatar_style": "normal",
                "scale": 3.1,
                "position": {
                    "x": 0,
                    "y": 0
                }
            },
            "voice": {
                "type": "audio",
                "audio_asset_id": audio_asset_ids[i]
            },
            "background": {
                "type": "color",
                "value": "#000000"
            }
        }
        video_inputs.append(input)
    
    payload = {
        "video_inputs": video_inputs,
        "dimension": {
            "width": 720,
            "height": 1280
        },
        "video_type": "vertical",
        "caption": True,
        "title": "Multiple Avatars Video"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        video_id = result.get("data", {}).get("video_id")
        print(f"Video generation started. Video ID: {video_id}")
        return video_id
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def check_video_status(api_key, video_id):
    if not video_id:
        print("No video ID provided.")
        return
    
    url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
    headers = {"X-Api-Key": api_key}
    
    while True:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("data", {}).get("status")
            
            if status == "completed":
                video_url = result.get("data", {}).get("video_url")
                print(f"Video generation completed. Video URL: {video_url}")
                break
            elif status == "failed":
                error = result.get("data", {}).get("error", "Unknown error")
                print(f"Video generation failed: {error}")
                break
            elif status == "processing" or status == "pending" or status == "waiting":
                print(f"Video status: {status}. Checking again in 10 seconds...")
                time.sleep(10)
            else:
                print(f"Unknown status: {status}")
                break
        else:
            print(f"Error checking status: {response.status_code} - {response.text}")
            break

def main():
    # API key
    api_key = "NzYzODNmNTI5ODYyNGMyYTg1NzFhNTNmOWY4M2Q4OTYtMTc0MDczMjczOQ=="
    
    # Avatar IDs
    avatar_1_id = "a7f27a8c3f954a54b599f04dff1ae4ac"
    avatar_2_id = "21095f74dfe9401a85d044c207d19f2b"
    
    # Audio file paths
    base_path = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/tests/test_heygen_4_angles_api/"
    audio_paths = [
        os.path.join(base_path, "part_1.mp3"),
        os.path.join(base_path, "part_2.mp3"),
        os.path.join(base_path, "part_3.mp3"),
        os.path.join(base_path, "part_4.mp3")
    ]
    
    # Avatar IDs to use for each audio file
    avatar_ids = [avatar_1_id, avatar_2_id, avatar_1_id, avatar_2_id]
    
    # Step 1: Upload all audio files and get asset IDs
    audio_asset_ids = []
    for audio_path in audio_paths:
        asset_id = upload_audio_file(api_key, audio_path)
        if not asset_id:
            print(f"Failed to upload audio file: {audio_path}")
            return
        audio_asset_ids.append(asset_id)
    
    # Step 2: Generate video with the uploaded audio assets
    video_id = generate_video_with_multiple_avatars(api_key, avatar_ids, audio_asset_ids)
    
    # Step 3: Check status
    check_video_status(api_key, video_id)

if __name__ == "__main__":
    main() 