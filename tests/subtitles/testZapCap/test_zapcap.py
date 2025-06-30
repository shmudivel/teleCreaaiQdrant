#!/usr/bin/env python3
"""
Simple ZapCap API script to add subtitles to a video using HTTP requests.
"""

import requests
import time
import sys
import os

# --- Configuration ---
# Get your API key from https://platform.zapcap.ai/dashboard/api-key
ZAPCAP_API_KEY = os.environ.get("ZAPCAP_API_KEY", "28cb84d698031664e4f4b0d5b7e722a089c5f2a77ed5d131229aa2b6158a7782")

# Get your template ID from https://platform.zapcap.ai/dashboard/templates
# A template defines the style of the subtitles.
ZAPCAP_TEMPLATE_ID = "14bcd077-3f98-465b-b788-1b628951c340"

ZAPCAP_HOST = "https://api.zapcap.ai"

# Asset URL
VIDEO_URL = "https://drive.google.com/uc?export=download&id=1pfH_7e-DS-Cdzq5gSIwmjmmlDfeIMOPY"

def submit_caption_request():
    """Submit caption request to ZapCap API"""
    if ZAPCAP_API_KEY == "YOUR_API_KEY" or ZAPCAP_TEMPLATE_ID == "YOUR_TEMPLATE_ID":
        print("❌ Please set your ZAPCAP_API_KEY and ZAPCAP_TEMPLATE_ID.")
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ZAPCAP_API_KEY
    }

    # 1. Upload video by URL
    print(">> Submitting video URL to ZapCap...")
    print(f">> Video URL: {VIDEO_URL}")

    upload_payload = {
        "url": VIDEO_URL
    }
    
    try:
        upload_response = requests.post(
            f"{ZAPCAP_HOST}/videos/url",
            headers=headers,
            json=upload_payload
        )
        upload_response.raise_for_status()
        video_id = upload_response.json()["id"]
        print(f"✅ >> Video submitted successfully!")
        print(f">> Video ID: {video_id}")
    except requests.exceptions.RequestException as e:
        print(f"❌ >> Error submitting video URL: {e}")
        if e.response:
            print(f">> Response: {e.response.text}")
        sys.exit(1)

    # 2. Create captioning task
    print("\n>> Creating captioning task...")
    
    task_payload = {
        "templateId": ZAPCAP_TEMPLATE_ID,
        "autoApprove": True,
        "language": "ru",
        "renderOptions": {
            "subsOptions": {
                "emoji": False,
                "emojiAnimation": False,
                "emphasizeKeywords": True,
                "animation": True,
                "punctuation": True,
                "displayWords": 2
            },
            "styleOptions": {
                "top": 40,
                "fontUppercase": False,
                "fontSize": 65,
                "fontWeight": 700,
                "fontColor": "#FFFFFF"
            }
        }
    }
    
    try:
        task_response = requests.post(
            f"{ZAPCAP_HOST}/videos/{video_id}/task",
            headers=headers,
            json=task_payload
        )
        task_response.raise_for_status()
        task_id = task_response.json()["taskId"]
        print(f"✅ >> Task created successfully!")
        print(f">> Task ID: {task_id}")
        return video_id, task_id
    except requests.exceptions.RequestException as e:
        print(f"❌ >> Error creating task: {e}")
        if e.response:
            print(f">> Response: {e.response.text}")
        sys.exit(1)


def check_caption_status(video_id, task_id):
    """Check the status of a captioning job"""
    headers = {
        "x-api-key": ZAPCAP_API_KEY
    }
    
    while True:
        try:
            response = requests.get(
                f"{ZAPCAP_HOST}/videos/{video_id}/task/{task_id}",
                headers=headers
            )
            response.raise_for_status()
            
            result = response.json()
            status = result.get("status")
            print(f">> Status: {status.upper()}")
            
            if status == "completed":
                video_url = result.get("downloadUrl")
                print(f"🎉 >> Video successfully rendered!")
                print(f">> Download URL: {video_url}")
                return video_url
            elif status == "failed":
                error = result.get("error", "Unknown error")
                print(f"❌ >> Rendering failed: {error}")
                sys.exit(1)
            
            print(">> Waiting 10 seconds before checking again...")
            time.sleep(10)

        except requests.exceptions.RequestException as e:
            print(f"❌ >> Error checking status: {e}")
            if e.response:
                print(f">> Response: {e.response.text}")
            sys.exit(1)

def main():
    """Main function"""
    print("=== ZapCap Subtitle Generation ===")
    
    # Submit caption request
    video_id, task_id = submit_caption_request()
    
    # Wait for completion
    if video_id and task_id:
        video_url = check_caption_status(video_id, task_id)
        print(f"\n🎉 SUCCESS! Your video with subtitles is ready:")
        print(f"📥 Download URL: {video_url}")

if __name__ == "__main__":
    main()
