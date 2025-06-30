#!/usr/bin/env python3
"""
IBM Plex Sans Bold 700 Main Subtitle Implementation
Clean example of using IBM Plex Sans Bold 700 from Google Fonts with thin black outline
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

# IBM Plex Sans Bold 700 from Google Fonts
IBM_PLEX_SANS_BOLD_URL = "https://fonts.gstatic.com/s/ibmplexsans/v19/zYXgKVElMYYaJe8bpLHnCwDKhdHeFaxOedfTDw.woff2"

def create_main_subtitle_payload():
    """Create payload with IBM Plex Sans Bold 700 as main subtitle with thin black outline"""
    payload = {
        "timeline": {
            "fonts": [
                {
                    "src": IBM_PLEX_SANS_BOLD_URL
                }
            ],
            "tracks": [
                # Main Subtitle Track - IBM Plex Sans Bold 700 with thin black outline
                {
                    "clips": [
                        {
                            "asset": {
                                "type": "caption",
                                "src": SRT_URL,
                                "width": 1000,
                                "font": {
                                    "family": "IBM Plex Sans",
                                    "size": 65,
                                    "color": "#FFFFFF",           # White text
                                    "stroke": "#000000",         # Black outline
                                    "strokeWidth": 1,            # Thin outline (1px)
                                    "weight": "700"              # Bold 700
                                }
                            },
                            "start": 0,
                            "length": "end",
                            "position": "center",
                            "offset": {
                                "x": 0,
                                "y": 0.25                        # Position in lower third
                            }
                        }
                    ]
                },
                # Video Track
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
            "aspectRatio": "9:16",
            "fps": 25,
            "quality": "high"
        }
    }
    return payload

def submit_render_request():
    """Submit render request to Shotstack API"""
    headers = {
        "Content-Type": "application/json",
        "x-api-key": SHOTSTACK_API_KEY
    }
    
    payload = create_main_subtitle_payload()
    
    print(">> Creating video with IBM Plex Sans Bold 700 main subtitles...")
    print(f">> Video URL: {VIDEO_URL}")
    print(f">> SRT URL: {SRT_URL}")
    print(f">> Font: IBM Plex Sans Bold 700 from Google Fonts")
    print(f">> Style: White text with thin black outline")
    
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
    print("=== IBM Plex Sans Bold 700 Main Subtitle Generator ===")
    print()
    print("📝 Subtitle Configuration:")
    print("   • Font: IBM Plex Sans Bold 700")
    print("   • Source: Google Fonts")
    print("   • Color: White (#FFFFFF)")
    print("   • Outline: Thin Black (1px)")
    print("   • Size: 65px")
    print("   • Position: Lower third")
    print()
    
    # Submit render request
    render_id = submit_render_request()
    
    # Wait for completion
    video_url = check_render_status(render_id)
    
    print(f"\n🎉 SUCCESS! Your video with IBM Plex Sans Bold 700 subtitles is ready:")
    print(f"📥 Download URL: {video_url}")
    print(f"\n💡 Font Configuration Used:")
    print(f"   • family: 'IBM Plex Sans'")
    print(f"   • weight: '700'")
    print(f"   • color: '#FFFFFF'")
    print(f"   • stroke: '#000000'")
    print(f"   • strokeWidth: 1")

if __name__ == "__main__":
    main() 