#!/usr/bin/env python3
"""
Simple Shotstack API script to add subtitles to video using HTTP requests
"""

import requests
import json
import time
import sys

# Configuration
SHOTSTACK_API_KEY = "7lYYstHdmRQoG2UuyIfoPcb2azzBZwXIjjTBi9Oa"
SHOTSTACK_HOST = "https://api.shotstack.io/stage"

# Asset URLs
VIDEO_URL = "https://drive.google.com/uc?export=download&id=1hFHrugey5soaMcQESHUisoA2FIbA9YaH"
SRT_URL = "https://gist.githubusercontent.com/shmudivel/0755e8bded9d5674064c9e48926c4c0a/raw/93f8bc0208efffcde49c02d0b30378f22609d286/subtitles.srt"
FONT_URL = "https://github.com/IBM/plex/raw/master/packages/plex-sans/fonts/complete/ttf/IBMPlexSans-SemiBold.ttf"

def create_render_payload():
    """Create the JSON payload for Shotstack render request"""
    payload = {
        "timeline": {
            "fonts": [
                {
                    "src": FONT_URL
                }
            ],
            "tracks": [
                {
                    "clips": [
                        {
                            "asset": {
                                "type": "caption",
                                "src": SRT_URL,
                                "width": 900,
                                "font": {
                                    "family": "IBM Plex Sans",
                                    "size": 70,
                                    "color": "#FFFFFF",
                                    "stroke": "#000000",
                                    "strokeWidth": 2
                                }
                            },
                            "start": 0,
                            "length": "end",
                            "position": "center",
                            "offset": {
                                "x": 0,
                                "y": 0.2
                            }
                        }
                    ]
                },
                {
                    "clips": [
                        {
                            "asset": {
                                "type": "video",
                                "src": VIDEO_URL
                            },
                            "start": 0,
                            "length": "auto"
                        }
                    ]
                }
            ]
        },
        "output": {
            "format": "mp4",
            "resolution": "1080",
            "aspectRatio": "9:16"
        }
    }
    return payload

def submit_render_request():
    """Submit render request to Shotstack API"""
    headers = {
        "Content-Type": "application/json",
        "x-api-key": SHOTSTACK_API_KEY
    }
    
    payload = create_render_payload()
    
    print(">> Submitting render request to Shotstack...")
    print(f">> Video URL: {VIDEO_URL}")
    print(f">> SRT URL: {SRT_URL}")
    print(f">> Font URL: {FONT_URL}")
    print(">> Using IBM Plex Sans Semi Bold 600")
    
    response = requests.post(
        f"{SHOTSTACK_HOST}/render",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 201:
        result = response.json()
        render_id = result["response"]["id"]
        print(f"✅ >> Render request submitted successfully!")
        print(f">> Render ID: {render_id}")
        return render_id
    else:
        print(f"❌ >> Error submitting request: {response.status_code}")
        print(f">> Response: {response.text}")
        sys.exit(1)

def check_render_status(render_id):
    """Check the status of a render job"""
    headers = {
        "Content-Type": "application/json",
        "x-api-key": SHOTSTACK_API_KEY
    }
    
    while True:
        response = requests.get(
            f"{SHOTSTACK_HOST}/render/{render_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result["response"]["status"]
            print(f">> Status: {status.upper()}")
            
            if status == "done":
                video_url = result["response"]["url"]
                print(f"🎉 >> Video successfully rendered!")
                print(f">> Download URL: {video_url}")
                return video_url
            elif status == "failed":
                error = result["response"].get("error", "Unknown error")
                print(f"❌ >> Rendering failed: {error}")
                sys.exit(1)
            
            print(">> Waiting 10 seconds before checking again...")
            time.sleep(10)
        else:
            print(f"❌ >> Error checking status: {response.status_code}")
            print(f">> Response: {response.text}")
            sys.exit(1)

def main():
    """Main function"""
    print("=== Shotstack Subtitle Generation ===")
    
    # Submit render request
    render_id = submit_render_request()
    
    # Wait for completion
    video_url = check_render_status(render_id)
    
    print(f"\n🎉 SUCCESS! Your video with subtitles is ready:")
    print(f"📥 Download URL: {video_url}")

if __name__ == "__main__":
    main()
