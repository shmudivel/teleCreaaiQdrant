#!/usr/bin/env python3
"""
Advanced Shotstack API script to create animated subtitles using HTML/CSS
Demonstrates font objects and HTML/CSS layering for animated captions
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

# Custom fonts for IBM Plex Sans Bold 700 (Cyrillic and Latin)
CUSTOM_FONTS = [
    {
        "family": "IBM Plex Sans",
        "weight": 700,
        "style": "normal",
        "src": "https://fonts.gstatic.com/s/ibmplexsans/v19/zYX9KVElMYYaJe8bpLHnCwDKjWr7AIFsdO3q.woff2", # Latin
    },
    {
        "family": "IBM Plex Sans",
        "weight": 700,
        "style": "normal",
        "src": "https://fonts.gstatic.com/s/ibmplexsans/v19/zYX9KVElMYYaJe8bpLHnCwDKjWr7AIJsdO3q.woff2", # Cyrillic
    },
    {
        "family": "IBM Plex Sans",
        "weight": 700,
        "style": "normal",
        "src": "https://fonts.gstatic.com/s/ibmplexsans/v19/zYX9KVElMYYaJe8bpLHnCwDKjWr7AI1sdO3q.woff2", # Cyrillic-ext
    }
]

# ==============================================================================
# IMPORTANT NOTE FOR SHOTSTACK SUPPORT
# ==============================================================================
# The following function `create_srt_payload` generates a payload that
# consistently fails with a 400 Bad Request error. The error message is:
# "timeline.tracks[1].clips[0].asset.type" must be [audio]
#
# This error is misleading, as we are trying to add a caption track, not audio.
# We have confirmed that:
#   - The video track must be the first track.
#   - Using a `font` object for styling is the correct approach for captions.
#   - All asset URLs (video, srt, fonts) are valid and accessible.
#
# We suspect this is a bug or an undocumented constraint in the API.
# Please find the generated JSON payload in the console output when running this
# script, and advise on a solution.
# ==============================================================================

def create_srt_payload():
    """Create the JSON payload for Shotstack render request with SRT captions."""
    payload = {
        "timeline": {
            "fonts": [{"src": font["src"]} for font in CUSTOM_FONTS],
            "tracks": [
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
                },
                {
                    "clips": [
                        {
                            "asset": {
                                "type": "caption",
                                "src": SRT_URL,
                                "font": {
                                    "family": "IBM Plex Sans",
                                    "size": 65,
                                    "color": "#FFFFFF",
                                    "stroke": "#000000",
                                    "strokeWidth": 1,
                                    "weight": "bold"
                                },
                                "width": 1000,
                                "background": "transparent"
                            },
                            "start": 0,
                            "length": "end",
                            "position": "bottom",
                            "offset": {
                                "x": 0,
                                "y": -0.15
                            }
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

def create_html_css_caption():
    """Create HTML/CSS animated caption content"""
    html_content = """
    <div class="subtitle-container">
        <div class="subtitle-text">IBM Plex Sans Bold 700 тест</div>
        <div class="subtitle-effect"></div>
    </div>
    """
    
    css_content = """
    @font-face {
        font-family: 'IBM Plex Sans';
        font-style: normal;
        font-weight: 700;
        src: url('https://fonts.gstatic.com/s/ibmplexsans/v22/zYXGKVElMYYaJe8bpLHnCwDKr932-G7dytD-Dmu1swZSAXcomDVmadSDDV5DB6g4tIOm6_De.woff2') format('woff2');
        unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
    }
    
    @font-face {
        font-family: 'IBM Plex Sans';
        font-style: normal;
        font-weight: 700;
        src: url('https://fonts.gstatic.com/s/ibmplexsans/v22/zYXGKVElMYYaJe8bpLHnCwDKr932-G7dytD-Dmu1swZSAXcomDVmadSDDV5DA6g4tIOm6_DeLVQ.woff2') format('woff2');
        unicode-range: U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116;
    }
    
    @font-face {
        font-family: 'IBM Plex Sans';
        font-style: normal;
        font-weight: 700;
        src: url('https://fonts.gstatic.com/s/ibmplexsans/v22/zYXGKVElMYYaJe8bpLHnCwDKr932-G7dytD-Dmu1swZSAXcomDVmadSDDV5DCqg4tIOm6_DeLVQ.woff2') format('woff2');
        unicode-range: U+0460-052F, U+1C80-1C8A, U+20B4, U+2DE0-2DFF, U+A640-A69F, U+FE2E-FE2F;
    }
    
    .subtitle-container {
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        height: 100%;
    }
    
    .subtitle-text {
        font-family: 'IBM Plex Sans', 'Arial', sans-serif;
        font-size: 48px;
        font-weight: 700;
        font-style: normal;
        color: #ffffff;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        animation: slideInUp 0.8s ease-out, glow 2s ease-in-out infinite alternate;
        z-index: 2;
        position: relative;
        font-feature-settings: "kern" 1;
        text-rendering: optimizeLegibility;
    }
    
    .subtitle-effect {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(45deg, rgba(255,0,150,0.3), rgba(0,150,255,0.3));
        border-radius: 10px;
        animation: pulse 2s ease-in-out infinite;
        z-index: 1;
    }
    
    @keyframes slideInUp {
        from {
            transform: translateY(100px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    @keyframes glow {
        from {
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8), 0 0 10px rgba(255,255,255,0.5);
        }
        to {
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8), 0 0 20px rgba(255,255,255,0.8), 0 0 30px rgba(255,255,255,0.6);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
            opacity: 0.3;
        }
        50% {
            transform: scale(1.05);
            opacity: 0.5;
        }
    }
    """
    
    return html_content, css_content

def create_animated_render_payload():
    """Create the JSON payload for Shotstack render request with animated captions"""
    html_content, css_content = create_html_css_caption()
    
    # Create a test subtitle with Russian text to verify font rendering
    test_subtitle_html = """
    <div class="test-subtitle">
        <div class="test-text">Проверка шрифта IBM Plex Sans Bold тест</div>
    </div>
    """
    
    test_subtitle_css = """
    @font-face {
        font-family: 'IBM Plex Sans';
        font-style: normal;
        font-weight: 700;
        src: url('https://fonts.gstatic.com/s/ibmplexsans/v22/zYXGKVElMYYaJe8bpLHnCwDKr932-G7dytD-Dmu1swZSAXcomDVmadSDDV5DB6g4tIOm6_De.woff2') format('woff2');
        unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
    }
    
    @font-face {
        font-family: 'IBM Plex Sans';
        font-style: normal;
        font-weight: 700;
        src: url('https://fonts.gstatic.com/s/ibmplexsans/v22/zYXGKVElMYYaJe8bpLHnCwDKr932-G7dytD-Dmu1swZSAXcomDVmadSDDV5DA6g4tIOm6_DeLVQ.woff2') format('woff2');
        unicode-range: U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116;
    }
    
    @font-face {
        font-family: 'IBM Plex Sans';
        font-style: normal;
        font-weight: 700;
        src: url('https://fonts.gstatic.com/s/ibmplexsans/v22/zYXGKVElMYYaJe8bpLHnCwDKr932-G7dytD-Dmu1swZSAXcomDVmadSDDV5DCqg4tIOm6_DeLVQ.woff2') format('woff2');
        unicode-range: U+0460-052F, U+1C80-1C8A, U+20B4, U+2DE0-2DFF, U+A640-A69F, U+FE2E-FE2F;
    }
    
    .test-subtitle {
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        height: 100%;
        padding: 20px;
    }
    
    .test-text {
        font-family: 'IBM Plex Sans', 'Arial', sans-serif;
        font-size: 65px;
        font-weight: 700;
        font-style: normal;
        color: #FFFFFF;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        background: rgba(0,0,0,0.2);
        padding: 10px 20px;
        border-radius: 8px;
        max-width: 90%;
        line-height: 1.2;
        font-feature-settings: "kern" 1;
        text-rendering: optimizeLegibility;
    }
    """
    
    payload = {
        "timeline": {
            "fonts": [
                {
                    "src": font["src"]
                } for font in CUSTOM_FONTS
            ],
            "tracks": [
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
                },
                {
                    "clips": [
                        {
                            "asset": {
                                "type": "html",
                                "html": test_subtitle_html,
                                "css": test_subtitle_css,
                                "width": 1080,
                                "height": 300,
                                "background": "transparent"
                            },
                            "start": 0,
                            "length": "end",
                            "position": "center",
                            "offset": {
                                "x": 0,
                                "y": 0.25
                            }
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

def create_font_showcase_payload():
    """Create a payload showcasing different font objects and styles"""
    payload = {
        "timeline": {
            "fonts": [
                {"src": font_url} for font_url in CUSTOM_FONTS
            ],
            "tracks": [
                # Video Track - Must be first
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
                },
                # Font Style 1: IBM Plex Sans Bold 700 with stroke (using HTML)
                {
                    "clips": [
                        {
                            "asset": {
                                "type": "html",
                                "html": "<div class='ibm-plex-bold'>IBM Plex Sans Bold 700 тест</div>",
                                "css": """
                                @font-face {
                                    font-family: 'IBM Plex Sans';
                                    font-style: normal;
                                    font-weight: 700;
                                    src: url('https://fonts.gstatic.com/s/ibmplexsans/v19/zYX9KVElMYYaJe8bpLHnCwDKjWr7AIxsdO3q.woff2') format('woff2');
                                    unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
                                }
                                
                                @font-face {
                                    font-family: 'IBM Plex Sans';
                                    font-style: normal;
                                    font-weight: 700;
                                    src: url('https://fonts.gstatic.com/s/ibmplexsans/v19/zYX9KVElMYYaJe8bpLHnCwDKjWr7AIJsdO3q.woff2') format('woff2');
                                    unicode-range: U+0460-052F, U+1C80-1C88, U+20B4, U+2DE0-2DFF, U+A640-A69F, U+FE2E-FE2F;
                                }
                                
                                .ibm-plex-bold {
                                    font-family: 'IBM Plex Sans', 'Arial', sans-serif;
                                    font-size: 80px;
                                    font-weight: 700;
                                    font-style: normal;
                                    color: #FF6B6B;
                                    text-align: center;
                                    text-shadow: 
                                        -4px -4px 0px #FFFFFF,
                                        4px -4px 0px #FFFFFF,
                                        -4px 4px 0px #FFFFFF,
                                        4px 4px 0px #FFFFFF;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    height: 100%;
                                    letter-spacing: -0.02em;
                                    font-feature-settings: "kern" 1;
                                    text-rendering: optimizeLegibility;
                                }
                                """,
                                "width": 1080,
                                "height": 200,
                                "background": "transparent"
                            },
                            "start": 0,
                            "length": 3,
                            "position": "center",
                            "offset": {
                                "x": 0,
                                "y": 0.3
                            }
                        }
                    ]
                },
                # Font Style 2: IBM Plex Sans with shadow (using HTML)
                {
                    "clips": [
                        {
                            "asset": {
                                "type": "html",
                                "html": "<div class='shadow-text'>IBM Plex Sans тест тень</div>",
                                "css": """
                                .shadow-text {
                                    font-family: 'IBM Plex Sans', 'Arial', sans-serif;
                                    font-size: 60px;
                                    font-weight: 700;
                                    font-style: normal;
                                    color: #4ECDC4;
                                    text-align: center;
                                    text-shadow: 5px 5px 10px rgba(0,0,0,0.8);
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    height: 100%;
                                    font-feature-settings: "kern" 1;
                                    text-rendering: optimizeLegibility;
                                }
                                """,
                                "width": 1080,
                                "height": 200,
                                "background": "transparent"
                            },
                            "start": 3,
                            "length": 3,
                            "position": "center",
                            "offset": {
                                "x": 0,
                                "y": 0.3
                            }
                        }
                    ]
                },
                # Font Style 3: Gradient effect (using HTML/CSS)
                {
                    "clips": [
                        {
                            "asset": {
                                "type": "html",
                                "html": "<div class='gradient-text'>IBM Plex Sans тест градиент</div>",
                                "css": """
                                .gradient-text {
                                    font-family: 'IBM Plex Sans', 'Arial', sans-serif;
                                    font-size: 72px;
                                    font-weight: 700;
                                    font-style: normal;
                                    background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4);
                                    background-size: 400% 400%;
                                    -webkit-background-clip: text;
                                    -webkit-text-fill-color: transparent;
                                    animation: gradientShift 3s ease infinite;
                                    text-align: center;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    height: 100%;
                                    font-feature-settings: "kern" 1;
                                    text-rendering: optimizeLegibility;
                                }
                                
                                @keyframes gradientShift {
                                    0% { background-position: 0% 50%; }
                                    50% { background-position: 100% 50%; }
                                    100% { background-position: 0% 50%; }
                                }
                                """,
                                "width": 1080,
                                "height": 200,
                                "background": "transparent"
                            },
                            "start": 6,
                            "length": 4,
                            "position": "center",
                            "offset": {
                                "x": 0,
                                "y": 0.3
                            }
                        }
                    ]
                },
                # Font Style 4: Main SRT subtitles - IBM Plex Sans Bold 700 with thin black outline
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
                                    "color": "#FFFFFF",
                                    "stroke": "#000000",
                                    "strokeWidth": 1,
                                    "weight": "bold"
                                }
                            },
                            "start": 10,
                            "length": "end",
                            "position": "center",
                            "offset": {
                                "x": 0,
                                "y": 0.25
                            }
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

def submit_render_request(payload_type="srt"):
    """Submit render request to Shotstack API"""
    headers = {
        "Content-Type": "application/json",
        "x-api-key": SHOTSTACK_API_KEY
    }
    
    if payload_type == "srt":
        payload = create_srt_payload()
        print(">> Creating SRT subtitles...")
    elif payload_type == "animated":
        payload = create_animated_render_payload()
        print(">> Creating animated captions with HTML/CSS...")
    else:
        payload = create_font_showcase_payload()
        print(">> Creating font showcase with different styles...")
    
    print("\n>> Generated Payload:")
    print(json.dumps(payload, indent=4))
    
    print(f"\n>> Video URL: {VIDEO_URL}")
    if payload_type == "srt":
        print(f">> SRT URL: {SRT_URL}")
    print(f">> Custom Fonts: {len(CUSTOM_FONTS)} fonts loaded")
    
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
    print("=== Shotstack IBM Plex Sans Caption Generation ===")
    print(">> Using IBM Plex Sans Bold 700 font exclusively")
    
    # Use SRT subtitles by default
    render_id = submit_render_request("srt")
    
    # Wait for completion
    video_url = check_render_status(render_id)
    
    print(f"\n🎉 SUCCESS! Your video with IBM Plex Sans captions is ready:")
    print(f"📥 Download URL: {video_url}")

if __name__ == "__main__":
    main() 