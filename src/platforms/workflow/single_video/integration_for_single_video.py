import os
import datetime
import json
import logging
import random
import requests
import re  # Add re module for regex operations
import time
import tempfile
import io
import shutil  # Added for copying file streams
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
from ..analyze_google_doc import extract_doc_id_from_url, get_document_content
# Import prompts from the single_video specific prompts file
from .prompts_for_single_video import (
    DOC_ANALYSIS_PROMPT, DOC_ANALYSIS_SYSTEM_PROMPT,
    REEL_GENERATION_PROMPT, REEL_GENERATION_SYSTEM_PROMPT,
    VIRAL_ANALYSIS_PROMPT, VIRAL_ANALYSIS_SYSTEM_PROMPT,
    FINAL_EDITING_PROMPT, FINAL_EDITING_SYSTEM_PROMPT,
    DEFAULT_EDIT_GUIDELINES, HOOK_VARIATIONS, CALL_TO_ACTION_VARIATIONS,
    HEYGEN_OPTIMIZATION_PROMPT, HEYGEN_OPTIMIZATION_SYSTEM_PROMPT,
    SCRIPT_VALIDATION_PROMPT, SCRIPT_VALIDATION_SYSTEM_PROMPT,
    NUMBER_CONVERSION_PROMPT, NUMBER_CONVERSION_SYSTEM_PROMPT
)
# Import API utilities from parent directory
from ..api_utils import call_claude_api, RateLimiter, exponential_backoff_retry, create_claude_client

# +++ Imports for audio cutting +++
from pydub import AudioSegment
from pydub.silence import detect_silence
# Import the audio_cutter module from parent directory
from ..audio_cutter import cut_audio_file
# +++ End imports for audio cutting +++

# +++ Imports for HeyGen video generation from the dedicated script +++
from ..generate_heygen_video import upload_audio_file, generate_video_with_multiple_avatars, check_video_status
# +++ End HeyGen imports +++

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
# Add ElevenLabs constants
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID")

# +++ HeyGen Specific Constants for Audio Asset Workflow +++
# Using the same API Key as defined above for HEYGEN_API_KEY
HEYGEN_AVATAR_ID_1 = "a7f27a8c3f954a54b599f04dff1ae4ac"  # From generate_heygen_video.py
HEYGEN_AVATAR_ID_2 = "21095f74dfe9401a85d044c207d19f2b"  # From generate_heygen_video.py
# +++ End HeyGen Specific Constants +++

# +++ Default cutting parameters (can be made configurable later) +++
DEFAULT_MIN_SILENCE_LEN_PARAM = 2200  # ms (Changed from 2800 to match audio_cutter.py)
DEFAULT_SILENCE_THRESH_PARAM = -46    # dBFS (This is not directly used by cut_audio_file's core logic but kept for potential future use)
DEFAULT_MIN_TARGET_SILENCE_DURATION = 2.2  # seconds (Changed from 3.0)
DEFAULT_MAX_TARGET_SILENCE_DURATION = 10.0  # seconds (Changed from 6.0)
DEFAULT_NUM_DESIRED_CUTS = 3 # Results in up to 4 parts
DEFAULT_END_OF_WORD_BUFFER_MS = 500 # ms (Changed from 700 to match audio_cutter.py)
# +++ End cutting parameters +++

def generate_audio_with_elevenlabs(script_text: str, output_dir: str, reel_title: str) -> Optional[str]:
    """
    Generates audio from script text using ElevenLabs API and saves it to a file.
    It then attempts to cut this audio file into parts based on silence.

    Args:
        script_text: The text (SSML-enhanced) to convert to speech.
        output_dir: The directory to save the generated audio file and its parts.
        reel_title: The title of the reel, used for naming the audio file.

    Returns:
        The path to the original (uncut) generated audio file, or None if generation failed.
        Cut parts are saved as a side effect in a subdirectory.
    """
    logger.info(f"Attempting to generate audio with ElevenLabs for: {reel_title}")

    if not ELEVENLABS_API_KEY:
        logger.error("ELEVENLABS_API_KEY not found in environment variables.")
        return None
    if not ELEVENLABS_VOICE_ID:
        logger.error("ELEVENLABS_VOICE_ID not found in environment variables.")
        return None

    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": script_text,
        "model_id": "eleven_multilingual_v2", # This model supports SSML
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    audio_path: Optional[str] = None # Define audio_path here for broader scope

    try:
        # Use a timeout for the request
        response = requests.post(tts_url, json=data, headers=headers, stream=True, timeout=300)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        # Sanitize reel_title for filename and limit length
        safe_title = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in reel_title).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50] # Limit length after sanitizing
        
        audio_filename = f"elevenlabs_audio_{safe_title}_{int(time.time())}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)
        
        with open(audio_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): 
                # filter out keep-alive new chunks
                if chunk: 
                    f.write(chunk)
        
        logger.info(f"Successfully generated ElevenLabs audio and saved to {audio_path}")

        # Now, attempt to cut the generated audio into parts
        # Create a specific subdirectory for the parts of this audio file
        parts_subdir_name = f"parts_{Path(audio_filename).stem}" # Use stem to avoid double .mp3
        parts_output_dir = os.path.join(output_dir, parts_subdir_name)
        Path(parts_output_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"Attempting to cut {audio_path} into parts, saving to {parts_output_dir}")
        
        # Use the imported cut_audio_file function from audio_cutter.py
        cut_audio_parts_paths = cut_audio_file(audio_path, parts_output_dir,
                                              min_silence_len_param=DEFAULT_MIN_SILENCE_LEN_PARAM,
                                              min_target_silence_duration=DEFAULT_MIN_TARGET_SILENCE_DURATION,
                                              max_target_silence_duration=DEFAULT_MAX_TARGET_SILENCE_DURATION,
                                              num_desired_cuts=DEFAULT_NUM_DESIRED_CUTS,
                                              end_of_word_buffer_ms=DEFAULT_END_OF_WORD_BUFFER_MS)
        
        if cut_audio_parts_paths:
            logger.info(f"Successfully processed audio cutting. {len(cut_audio_parts_paths)} parts generated in {parts_output_dir}:")
            for part_p in cut_audio_parts_paths:
                logger.info(f"  - {part_p}")
        else:
            logger.warning(f"Audio cutting did not produce parts for {audio_path}, or an error occurred during cutting. Check previous logs.")
            # The original audio_path is still valid and will be returned.

        return audio_path # Return the path to the original, uncut audio file

    except requests.exceptions.HTTPError as http_err:
        # Accessing response.text here might be problematic if the error occurred before response was fully received
        # or if response is not available in this scope due to earlier error.
        # Let's ensure response is defined or provide a generic message.
        error_detail = ""
        if 'response' in locals() and hasattr(response, 'text'):
            error_detail = f" - {response.text}"
        logger.error(f"ElevenLabs API request failed with HTTP error: {http_err}{error_detail}")
        return None
    except requests.exceptions.RequestException as req_err:
        logger.error(f"ElevenLabs API request error: {req_err}")
        return None
    except Exception as e:
        # If audio_path was set and an error happens during cutting, we might still have the original.
        # However, the function expects to return Optional[str] for the *original* audio.
        # If the error is in cutting, the original audio might still be fine.
        logger.error(f"An unexpected error occurred: {e}")
        if audio_path and os.path.exists(audio_path) and isinstance(e, (FileNotFoundError, Exception)) and "pydub" in str(e).lower() : # Check if error is from pydub
             logger.warning(f"Error occurred during audio cutting phase for {audio_path}. Original audio is likely intact.")
             return audio_path # Return original if cutting failed but generation was ok
        return None

def suggest_next_topic(
    all_reels: List[Dict[str, Any]],
    processed_reel_identifiers: List[str],
    identifier_key: str = 'title'
) -> Optional[Dict[str, Any]]:
    """
    Suggests the next reel topic for audio generation from a list of all reels,
    excluding those that have already been processed.

    Args:
        all_reels: A list of dictionaries, where each dictionary represents a reel
                   and contains at least an identifier key (e.g., 'title').
        processed_reel_identifiers: A list of identifiers (e.g., titles or filenames)
                                    of reels for which audio has already been generated.
        identifier_key: The key in the reel dictionary to use for matching against
                        processed_reel_identifiers. Defaults to 'title'.

    Returns:
        A dictionary representing the suggested reel, or None if all reels have been processed
        or no unprocessed reels are found.
    """
    logger.info(f"Attempting to suggest next topic. Total reels: {len(all_reels)}, Processed: {len(processed_reel_identifiers)}")

    unprocessed_reels = []
    for reel in all_reels:
        reel_identifier = reel.get(identifier_key)
        if reel_identifier and reel_identifier not in processed_reel_identifiers:
            unprocessed_reels.append(reel)

    if not unprocessed_reels:
        logger.info("No more unprocessed topics to suggest.")
        return None

    # Suggest the first one from the list of unprocessed reels
    suggested_reel = unprocessed_reels[0]
    logger.info(f"Suggesting next topic: {suggested_reel.get(identifier_key, 'Unknown Topic')}")
    return suggested_reel

def process_google_doc_for_single_video(url: str, service_account_file: str) -> str:
    """Process a Google Doc and prepare it for a single video.
    
    Args:
        url: Google Doc URL
        service_account_file: Path to service account JSON file
    
    Returns:
        Path to the created analyzed text file
    """
    logger.info("Step 1: Analyzing Google Doc for single video")
    logger.info(f"Extracting content from: {url}")
    
    # Extract document ID from URL
    doc_id = extract_doc_id_from_url(url)
    logger.info(f"Document ID: {doc_id}")
    
    # Get document content
    content = get_document_content(doc_id, service_account_file)
    logger.info(f"Retrieved {len(content)} characters from the document")
    
    # Create output directory if it doesn't exist
    script_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save the original content directly first - this is important to preserve exactly what was in the doc
    original_output_file = os.path.join(script_dir, f"original_doc_content_{timestamp}.txt")
    with open(original_output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Original document content saved to {original_output_file}")
    
    # Now analyze with Claude (but we'll use the original content file for processing)
    logger.info("Analyzing content with Claude for single video...")
    analyzed_text = analyze_with_claude(content)
    
    # Create output file for analyzed content
    output_file = os.path.join(script_dir, f"analyzed_doc_single_video_{timestamp}.txt")
    
    # Write the analyzed text to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(analyzed_text)
    
    logger.info(f"Analysis for single video written to {output_file}")
    
    # Return the original content file instead of the analyzed one
    # This ensures we're using the exact original content from the Google Doc
    return original_output_file

def create_single_video_script(input_file: str, output_dir: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Create a single video script from document content file.
    
    Args:
        input_file: Path to document content file
        output_dir: Directory to save output
        api_key: Anthropic API key (optional)
    
    Returns:
        Dictionary with paths to generated content and script data
    """
    logger.info("Step 2: Generating single video script")
    logger.info(f"Using document content from: {input_file}")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Create generator
    generator = SingleVideoGenerator(
        api_key=api_key,
        output_dir=output_dir
    )
    
    # Process the file to generate a single video script
    result = generator.process_file(input_file)
    
    logger.info(f"Single video script generated and saved to {output_dir}")
    return result

def process_google_doc_to_single_video(doc_url: str, output_dir: Optional[str] = None) -> Dict[str, str]:
    """Process a Google Doc and convert it to a single video.
    
    This is the main function that combines all the steps of the single video workflow.
    
    Args:
        doc_url: URL of the Google Doc to process
        output_dir: Directory to save output files (optional)
        
    Returns:
        Dictionary with paths to generated content
    """
    # Use edit guidelines from prompts.py
    edit_prompt = DEFAULT_EDIT_GUIDELINES
    
    # Create output directory if not provided
    if not output_dir:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"output_single_video_{timestamp}"
        
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Step 1: Process Google Doc for single video
        analyzed_doc_path = process_google_doc_for_single_video(doc_url, SERVICE_ACCOUNT_PATH)
        
        # Step 2: Generate single video script
        single_video_script_data = create_single_video_script(analyzed_doc_path, output_dir, ANTHROPIC_API_KEY)
        
        # Step 3: Final single video editing
        final_script_data = final_single_video_editing(
            script_data=single_video_script_data["script_data"],
            output_dir=output_dir,
            edit_prompt=edit_prompt,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 4: Validate and fix script
        validated_data = validate_single_video_script(
            final_script_data=final_script_data,
            output_dir=output_dir,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 5: Convert numbers to words
        converted_data = convert_numbers_in_single_video(
            validated_data=validated_data,
            output_dir=output_dir,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 6: Optimize script for HeyGen
        optimized_data = optimize_single_video_script(
            converted_data=converted_data,
            output_dir=output_dir,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 7: AUTOMATICALLY GENERATE VIDEO using ElevenLabs + HeyGen + YouTube upload
        logger.info("Step 7: Automatically generating video with ElevenLabs, HeyGen, and uploading to YouTube")
        video_generation_success = process_selected_reel(optimized_data["script_data"])
        
        if video_generation_success:
            logger.info("✅ Single video generation and upload completed successfully!")
        else:
            logger.error("❌ Video generation failed. Check logs for details.")
        
        # Return paths to various directories and files for reference
        return {
            "analyzed_doc_path": analyzed_doc_path,
            "script_data_dir": single_video_script_data["metadata_dir"],
            "final_script_dir": final_script_data["final_script_dir"],
            "validated_script_dir": validated_data["validated_dir"],
            "converted_script_dir": converted_data["converted_dir"],
            "optimized_script_dir": optimized_data["optimized_dir"],
            "final_script_json": final_script_data["json_path"],
            "final_script_text": final_script_data["text_path"],
            "optimized_script_json": optimized_data["json_path"],
            "optimized_script_text": optimized_data["text_path"],
            "optimized_script_data": optimized_data["script_data"],
            "video_generation_success": video_generation_success
        }
    
    except Exception as e:
        logger.error(f"An error occurred in the single video workflow: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise

# +++ New HeyGen functions for audio asset workflow +++
def upload_single_audio_to_heygen(api_key: str, audio_path: str) -> Optional[str]:
    """Upload an audio file to HeyGen and get the asset ID."""
    url = "https://upload.heygen.com/v1/asset"
    headers = {"X-Api-Key": api_key, "Content-Type": "audio/mpeg"}
    
    logger.info(f"Uploading audio file to HeyGen: {audio_path}")
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found for upload: {audio_path}")
        return None
        
    try:
        with open(audio_path, "rb") as audio_file:
            response = requests.post(url, headers=headers, data=audio_file, timeout=120)
        response.raise_for_status()
        result = response.json()
        if "data" in result and "id" in result["data"]:
            asset_id = result["data"]["id"]
            logger.info(f"HeyGen audio uploaded successfully. Asset ID: {asset_id} for {audio_path}")
            return asset_id
        else:
            logger.error(f"Error: Invalid HeyGen upload response format: {result} for {audio_path}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error uploading audio to HeyGen {audio_path}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"HeyGen Response: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error uploading audio to HeyGen {audio_path}: {e}")
        return None

def create_video_from_cut_audio_parts(reel_metadata: Dict, cut_audio_parts_dir: str) -> Optional[str]:
    """
    Orchestrates creating a HeyGen video from pre-cut audio parts.
    Uploads audio parts, generates video with alternating avatars, and polls for status.
    """
    api_key = HEYGEN_API_KEY # Use the globally defined key
    if not api_key:
        logger.error("HEYGEN_API_KEY not found in environment variables for create_video_from_cut_audio_parts.")
        return None

    title = reel_metadata.get('title', 'Untitled HeyGen Video')
    logger.info(f"Starting HeyGen video creation for '{title}' using audio parts from: {cut_audio_parts_dir}")

    if not os.path.isdir(cut_audio_parts_dir):
        logger.error(f"Cut audio parts directory not found: {cut_audio_parts_dir}")
        return None

    audio_part_files = sorted([
        os.path.join(cut_audio_parts_dir, f)
        for f in os.listdir(cut_audio_parts_dir)
        if f.startswith("part_") and f.endswith(".mp3")
    ], key=lambda x: int(re.search(r'part_(\d+)\.mp3', x).group(1))) # Sort by part number

    if not audio_part_files:
        logger.error(f"No audio part_*.mp3 files found in {cut_audio_parts_dir}")
        return None
    
    logger.info(f"Found {len(audio_part_files)} audio parts for '{title}': {audio_part_files}")

    audio_asset_ids = []
    for part_path in audio_part_files:
        asset_id = upload_single_audio_to_heygen(api_key, part_path)
        if asset_id:
            audio_asset_ids.append(asset_id)
        else:
            logger.error(f"Failed to upload audio part {part_path} for '{title}'. Aborting HeyGen video creation.")
            return None # If one part fails, abort.

    if not audio_asset_ids: # Should be caught by the None check above, but as a safeguard
        logger.error(f"No audio assets were successfully uploaded for '{title}'.")
        return None

    # Define the avatar cycle
    avatar_cycle = [HEYGEN_AVATAR_ID_1, HEYGEN_AVATAR_ID_2]
    
    video_id = generate_video_with_multiple_avatars(api_key, avatar_ids=avatar_cycle, audio_asset_ids=audio_asset_ids)
    if not video_id:
        logger.error(f"Failed to initiate HeyGen video generation for '{title}'.")
        return None

    # Poll for video completion
    final_video_url = check_video_status(api_key, video_id)
    if final_video_url:
        logger.info(f"Successfully generated HeyGen video for '{title}'. URL: {final_video_url}")
        # Here, you might want to trigger the next steps like uploading to Drive/YouTube.
        # For now, this function just returns the URL.
        # The existing process_selected_reel in integration.py handles Drive/YT upload for text-to-speech HeyGen.
        # This new flow focuses on generating the HeyGen video with audio assets.
        # The bot.py will need to handle what to do with this URL.
        
        # Let's integrate the Drive and YouTube upload here for consistency with the original process_selected_reel
        drive_info = upload_to_drive(final_video_url, f"{title.replace(' ', '_')[:30]}_HeyGenAudio.mp4", title)
        if not drive_info:
            logger.error(f"Failed to upload HeyGen video for '{title}' to Google Drive. Video URL was: {final_video_url}")
            # Still return the HeyGen URL as the video was generated.
            return final_video_url 

        temp_video_path = drive_info.get('temp_path')
        drive_file_id = drive_info.get('file_id')

        try:
            if not temp_video_path or not os.path.exists(temp_video_path):
                 # If temp_path is not valid (e.g. from upload_to_drive if it only returned ID)
                 # we need to download it again using file_id for YouTube upload
                 logger.info(f"Temporary video path not available or invalid for {title}, re-downloading from Drive ID: {drive_file_id}")
                 if drive_file_id:
                     temp_video_path = download_from_drive(drive_file_id) # This returns a new temp_path
                 else:
                     logger.error(f"Cannot download for YouTube upload, Drive file ID missing for {title}")
                     return final_video_url # Return HeyGen URL

            if temp_video_path and os.path.exists(temp_video_path):
                youtube_description = reel_metadata.get('description', f"Video for {title}")
                youtube_tags = reel_metadata.get('hashtags', [])
                
                youtube_video_id = upload_to_youtube(temp_video_path, title, youtube_description, youtube_tags)
                if youtube_video_id:
                    logger.info(f"Successfully uploaded HeyGen video for '{title}' to YouTube. YouTube ID: {youtube_video_id}")
                    return f"https://www.youtube.com/watch?v={youtube_video_id}" # Return YouTube URL
                else:
                    logger.error(f"Failed to upload HeyGen video for '{title}' to YouTube. HeyGen URL: {final_video_url}")
            else:
                logger.error(f"Could not obtain local video file for YouTube upload of '{title}'. HeyGen URL: {final_video_url}")
        
        finally:
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                    logger.info(f"Cleaned up temporary video file: {temp_video_path}")
                except OSError as e:
                    logger.error(f"Error deleting temporary video file {temp_video_path}: {e}")
        
        return final_video_url # Fallback to HeyGen URL if YouTube upload fails
    else:
        logger.error(f"HeyGen video for '{title}' did not complete or failed.")
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
    
    # Authenticate with Google Drive
    credentials_path = SERVICE_ACCOUNT_PATH
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

def download_from_drive(file_id):
    """Download video from Google Drive using service account authentication."""
    logger.info(f"Downloading video from Google Drive (File ID: {file_id})...")
    
    # Use service account credentials
    credentials_path = SERVICE_ACCOUNT_PATH
    scopes = ['https://www.googleapis.com/auth/drive.readonly']
    credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
    
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
        elif isinstance(tags, str):
            # If tags is a string, convert it to a list by splitting on spaces
            # Handle both comma-separated and space-separated hashtags
            import re
            tags = re.findall(r'#\w+', tags)  # Extract all hashtags from the string

        # Ensure tags is a list
        if not isinstance(tags, list):
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
    
    # Try to find token file in multiple locations
    token_paths = [
        TOKEN_FILE,  # Default location
        os.path.join(os.path.dirname(os.path.abspath(__file__)), TOKEN_FILE),  # Same directory as this file
        os.path.join(os.getcwd(), TOKEN_FILE),  # Current working directory
        os.environ.get("YOUTUBE_TOKEN_PATH", "")  # Environment variable
    ]
    
    token_file_path = None
    for path in token_paths:
        if path and os.path.exists(path):
            token_file_path = path
            logger.info(f"Found YouTube token file at: {path}")
            break
    
    try:
        client_secrets_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json').name
        with open(client_secrets_file, "w") as f:
            json.dump(client_config, f)
        
        # Use a simple token JSON file
        if token_file_path:
            with open(token_file_path, 'r') as token_file:
                token_data = json.load(token_file)
                credentials = Credentials.from_authorized_user_info(token_data)
                logger.info("Using stored YouTube credentials, no browser authentication needed")
        
        # If credentials don't exist or are invalid, we need to create new ones
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                logger.info("Refreshing expired credentials...")
                credentials.refresh(Request())
            else:
                msg = "No valid YouTube credentials found. Need browser authentication (one-time setup)."
                logger.error(msg)
                raise RuntimeError(msg + " This requires a machine with a web browser.")
        
        return build("youtube", "v3", credentials=credentials)
    
    finally:
        # Clean up client secrets
        if 'client_secrets_file' in locals() and os.path.exists(client_secrets_file):
            os.remove(client_secrets_file)

# +++ End New HeyGen functions +++ 

def analyze_with_claude(text, api_key=None):
    """
    Analyze text content with Claude to prepare it for a single video script.
    
    Args:
        text: The text content to analyze
        api_key: Anthropic API key (optional)
    
    Returns:
        The analyzed text prepared for a single video script
    """
    logger.info("Analyzing content with Claude...")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Get Claude client
    client = create_claude_client(api_key)
    
    # First, ensure we have the original text saved separately
    original_text = text
    
    # Create a more explicit prompt
    enhanced_prompt = f"""Analyze the following text and prepare it for scripting a single, coherent YouTube video.
    
Identify the main theme, key arguments, and logical flow of the content. 
The goal is to understand the document's structure to create one continuous video script.

CRITICAL INSTRUCTION: Your ONLY task is to analyze the structure. DO NOT modify, summarize or change the text in ANY way.
You MUST return the EXACT original text.

Original Text:
'''
{text}
'''

Again: RETURN THE EXACT ORIGINAL TEXT WITHOUT ANY CHANGES OR ANALYSIS ADDED. The structure analysis is performed internally only."""
    
    # Call Claude with retry logic
    result = call_claude_api(
        client=client,
        model="claude-3-7-sonnet-20250219",
        prompt=enhanced_prompt,
        system=DOC_ANALYSIS_SYSTEM_PROMPT,
        max_tokens=50000,  # Reduced from 100000, still large enough for most docs
        temperature=0.2,
        stream=True  # Explicitly enable streaming to avoid timeout errors
    )
    
    # Check if Claude returned something very different from the original
    # (allow for some minor whitespace differences)
    if len(result.strip()) < len(original_text.strip()) * 0.9:
        logger.warning("Claude's response appears to be significantly shorter than the original text.")
        logger.warning("Using original text instead of Claude's response to ensure content integrity.")
        return original_text
    
    logger.info("Analysis completed successfully.")
    return result

class SingleVideoGenerator:
    """Class for generating a single video script from analyzed text."""
    
    def __init__(self, api_key=None, output_dir=None):
        """Initialize the generator.
        
        Args:
            api_key: Anthropic API key (optional)
            output_dir: Directory to save output (optional)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.output_dir = output_dir or "output_single_video"
        
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Get Anthropic client
        self.client = create_claude_client(self.api_key)
    
    def read_analyzed_text(self, filepath):
        """Read analyzed text from a file.
        
        Args:
            filepath: Path to the analyzed text file
            
        Returns:
            The text content of the file
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate_video_script(self, text):
        """Generate a single video script from analyzed text.
        
        Args:
            text: The analyzed text content
            
        Returns:
            Dictionary with video script data
        """
        logger.info("Generating single video script...")
        
        # Call Claude to generate the script
        result = call_claude_api(
            client=self.client,
            model="claude-3-7-sonnet-20250219",
            prompt=REEL_GENERATION_PROMPT.format(content=text),
            system=REEL_GENERATION_SYSTEM_PROMPT,
            max_tokens=4000,
            temperature=0.7,
            stream=True  # Enable streaming for reliability
        )
        
        # Parse the JSON response
        try:
            script_data = json.loads(result)
            logger.info("Video script generated successfully.")
            return script_data
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Raw response: {result}")
            # Create a basic structure if JSON parsing fails
            return {
                "heygen_script": result,
                "title": "Single Video Script",
                "hashtags": ["#SingleVideo"],
                "description": "Generated video script"
            }
    
    def save_video_script(self, script_data):
        """Save the video script to files.
        
        Args:
            script_data: Dictionary with script data
            
        Returns:
            Dictionary with paths to saved files
        """
        # Create metadata directory
        metadata_dir = os.path.join(self.output_dir, "metadata")
        Path(metadata_dir).mkdir(parents=True, exist_ok=True)
        
        # Save JSON metadata
        json_path = os.path.join(metadata_dir, "single_video_script.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)
        
        # Save plain text script
        text_path = os.path.join(metadata_dir, "single_video_script.txt")
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(f"# {script_data.get('title', 'Single Video Script')}\n\n")
            f.write(script_data.get('heygen_script', ''))
        
        logger.info(f"Video script saved to {json_path} and {text_path}")
        
        return {
            "metadata_dir": metadata_dir,
            "json_path": json_path,
            "text_path": text_path,
            "script_data": script_data
        }
    
    def process_file(self, input_filepath):
        """Process an analyzed text file to generate a single video script.
        
        Args:
            input_filepath: Path to the text file containing document content
            
        Returns:
            Dictionary with paths to generated content
        """
        # Read the text
        logger.info(f"Processing file for video generation: {input_filepath}")
        text = self.read_analyzed_text(input_filepath)
        logger.info(f"Read {len(text)} characters from file")
        
        # Generate the script
        script_data = self.generate_video_script(text)
        
        # Save the script
        return self.save_video_script(script_data)

class SingleVideoWorkflowTasks:
    """Tasks for content workflow from Google Docs to a single YouTube video."""
    
    def google_doc_to_single_video_task(self, doc_url, output_dir=None):
        """
        Process a Google Doc and convert it to a single video
        
        Args:
            doc_url: URL of the Google Doc to process
            output_dir: Directory to save output files (optional)
            
        Returns:
            Dictionary with paths to generated content
        """
        return process_google_doc_to_single_video(doc_url, output_dir)
        
    def process_optimized_video_script(self, script_data):
        """
        Process an optimized video script - generate HeyGen video and upload to YouTube
        
        Args:
            script_data: The script data dictionary with optimized script
            
        Returns:
            Boolean indicating success or failure
        """
        return process_selected_reel(script_data) 

@exponential_backoff_retry()
def edit_single_video_script(client, script_data, edit_prompt, hook_variant, call_to_action_variant, model="claude-3-7-sonnet-20250219"):
    """Edit a single video script with retry logic."""
    script = script_data.get('heygen_script', '')
    title = script_data.get('title', '')
    
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
        max_tokens=4000,  # Increased for longer single video scripts
        temperature=0.7,
        stream=True  # Enable streaming for reliability
    )
    
    return result.strip()

def final_single_video_editing(script_data: Dict[str, Any], output_dir: str, edit_prompt: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Apply final edits to the single video script to improve engagement.
    
    Args:
        script_data: Dictionary with script data
        output_dir: Directory to save output
        edit_prompt: Instructions for editing the script
        api_key: Anthropic API key (optional)
    
    Returns:
        Dictionary with paths to edited script files
    """
    logger.info("Step 3: Final single video editing")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Get Anthropic client
    client = create_claude_client(api_key)
    
    # Define output directory
    final_script_dir = os.path.join(output_dir, "final_script")
    
    # Create output directory path
    Path(final_script_dir).mkdir(parents=True, exist_ok=True)
    
    # Create rate limiter to avoid hitting API limits
    rate_limiter = RateLimiter(calls_per_minute=10)
    
    # Select a random hook variant and call to action variant
    hook_variant = random.choice(HOOK_VARIATIONS)
    call_to_action_variant = random.choice(CALL_TO_ACTION_VARIATIONS)
    
    try:
        # Use rate limiter to prevent hitting API limits
        with rate_limiter:
            # Call Claude to edit the script
            logger.info("Editing single video script...")
            edited_script = edit_single_video_script(client, script_data, edit_prompt, hook_variant, call_to_action_variant)
        
        # Update the script data
        script_data['original_script'] = script_data.get('heygen_script', '')
        script_data['heygen_script'] = edited_script
        script_data['hook_variant'] = hook_variant
        script_data['call_to_action_variant'] = call_to_action_variant
        
        # Save the edited script metadata
        output_path = os.path.join(final_script_dir, "final_single_video_script.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)
        
        # Also save as a plain text file for heygen
        title = script_data.get('title', '')
        heygen_path = os.path.join(final_script_dir, "final_single_video_script.txt")
        with open(heygen_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n{edited_script}")
        
        logger.info(f"Saved edited single video script to {output_path}")
        
        return {
            "final_script_dir": final_script_dir,
            "json_path": output_path,
            "text_path": heygen_path,
            "script_data": script_data
        }
        
    except Exception as e:
        logger.error(f"Error editing single video script: {str(e)}")
        raise

def process_selected_reel(metadata):
    """Process the selected reel - generate HeyGen video and upload to YouTube."""
    
    # Ensure we're using the final script with all optimizations applied
    if 'pre_conversion_script' in metadata:
        logger.info("Using converted script with numbers as words for optimal HeyGen delivery")
    elif 'pre_validation_script' in metadata:
        logger.warning("Using validated script but without number conversion - consider adding number conversion step")
    elif 'original_script' in metadata:
        logger.warning("Using only optimized script without validation or number conversion - consider adding these steps")
    
    script = metadata.get("heygen_script")
    title = metadata.get("title", "Untitled HeyGen Video")

    if not script:
        logger.error("No heygen_script found in metadata for process_selected_reel.")
        return False

    video_url = None
    temp_audio_dir = None
    audio_file_path_for_tts = None

    try:
        # Step 1a: Generate audio from script using ElevenLabs
        logger.info(f"Generating audio for '{title}' using ElevenLabs for HeyGen text-to-video flow.")
        # Create a temporary directory for the audio file
        # Base the temp dir on metadata filename if possible to keep outputs somewhat organized
        metadata_filename = metadata.get('filename')
        base_output_dir_for_audio = os.path.dirname(metadata_filename) if metadata_filename and os.path.isabs(metadata_filename) else tempfile.gettempdir()
        
        # Create a specific subdir for this TTS audio to avoid filename clashes and for easier cleanup
        temp_audio_parent_dir = os.path.join(base_output_dir_for_audio, "temp_tts_for_heygen")
        Path(temp_audio_parent_dir).mkdir(parents=True, exist_ok=True)
        # Individual temp dir for this specific audio generation call
        temp_audio_dir = tempfile.mkdtemp(dir=temp_audio_parent_dir)

        audio_file_path_for_tts = generate_audio_with_elevenlabs(script, temp_audio_dir, title)

        if not audio_file_path_for_tts:
            logger.error(f"Failed to generate audio using ElevenLabs for '{title}'.")
            return False

        # Step 1b: Check for cut audio parts and use multi-avatar approach if available
        audio_filename_stem = Path(audio_file_path_for_tts).stem
        parts_subdir_name = f"parts_{audio_filename_stem}"
        cut_parts_dir = os.path.join(temp_audio_dir, parts_subdir_name)
        
        # Initialize variables for the fallback logic
        audio_part_files = []
        audio_asset_ids = []
        
        # Check if cut audio parts exist
        if os.path.isdir(cut_parts_dir):
            # Find all cut audio parts
            audio_part_files = sorted([
                os.path.join(cut_parts_dir, f)
                for f in os.listdir(cut_parts_dir)
                if f.startswith("part_") and f.endswith(".mp3")
            ], key=lambda x: int(re.search(r'part_(\d+)\.mp3', x).group(1)))
            
            if audio_part_files:
                logger.info(f"Found {len(audio_part_files)} cut audio parts. Using multi-avatar approach with alternating avatars.")
                
                # Step 1b1: Upload each audio part to HeyGen
                audio_asset_ids = []
                for part_path in audio_part_files:
                    asset_id = upload_single_audio_to_heygen(HEYGEN_API_KEY, part_path)
                    if asset_id:
                        audio_asset_ids.append(asset_id)
                    else:
                        logger.error(f"Failed to upload audio part {part_path} for '{title}'. Falling back to single audio approach.")
                        audio_asset_ids = []  # Clear and fall back
                
                if audio_asset_ids:
                    # Step 1b2: Create avatar cycle for multiple cameras/avatars
                    avatar_cycle = []
                    for i in range(len(audio_asset_ids)):
                        avatar_cycle.append(HEYGEN_AVATAR_ID_1 if i % 2 == 0 else HEYGEN_AVATAR_ID_2)
                    
                    # Step 1b3: Generate HeyGen video using multiple audio assets and avatars
                    logger.info(f"Generating HeyGen video for '{title}' using {len(audio_asset_ids)} audio parts with alternating avatars.")
                    video_id_response = generate_video_with_multiple_avatars(
                        HEYGEN_API_KEY,
                        avatar_ids=avatar_cycle,
                        audio_asset_ids=audio_asset_ids
                    )
                    
                    video_id = video_id_response
                    
                    if video_id:
                        logger.info(f"HeyGen video generation started for '{title}' with multi-avatar approach. Video ID: {video_id}")
                    else:
                        logger.error(f"Failed to start HeyGen video generation for '{title}' with multi-avatar approach. Falling back to single audio.")
                        audio_asset_ids = []  # Force fallback
        
        # Fallback to single audio approach if cut parts not found or failed
        if not os.path.isdir(cut_parts_dir) or not audio_part_files or not audio_asset_ids:
            logger.info(f"Using single audio approach for '{title}' (cut parts not available or failed).")
            
            # Step 1b (fallback): Upload single audio to HeyGen
            logger.info(f"Uploading generated audio '{audio_file_path_for_tts}' to HeyGen.")
            audio_asset_id = upload_audio_file(HEYGEN_API_KEY, audio_file_path_for_tts)

            if not audio_asset_id:
                logger.error(f"Failed to upload audio asset to HeyGen for '{title}'.")
                return False

            # Step 1c (fallback): Generate HeyGen video using single audio asset
            logger.info(f"Generating HeyGen video for '{title}' using single audio asset ID '{audio_asset_id}'.")
            video_id_response = generate_video_with_multiple_avatars(
                HEYGEN_API_KEY,
                avatar_ids=[HEYGEN_AVATAR_ID_1], # Single avatar
                audio_asset_ids=[audio_asset_id]  # Single audio asset
            )
            
            video_id = video_id_response

            if not video_id:
                logger.error(f"Failed to start HeyGen video generation for '{title}'.")
                return False
            
            logger.info(f"HeyGen video generation started for '{title}' with single avatar approach. Video ID: {video_id}")

        # Step 1d: Check video status (same for both approaches)
        video_url = check_video_status(HEYGEN_API_KEY, video_id)
        
        if not video_url:
            logger.error(f"HeyGen video generation failed or did not complete for '{title}'.")
            return False

    except Exception as e:
        logger.error(f"Error during HeyGen video generation pipeline for '{title}': {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        # Clean up temporary audio file and directory
        if audio_file_path_for_tts and os.path.exists(audio_file_path_for_tts):
            try:
                os.remove(audio_file_path_for_tts)
                logger.info(f"Removed temporary TTS audio file: {audio_file_path_for_tts}")
            except OSError as e:
                logger.error(f"Error removing temporary TTS audio file {audio_file_path_for_tts}: {e}")
        if temp_audio_dir and os.path.exists(temp_audio_dir):
            try:
                shutil.rmtree(temp_audio_dir) # Use shutil.rmtree for directory
                logger.info(f"Removed temporary TTS audio directory: {temp_audio_dir}")
            except OSError as e:
                logger.error(f"Error removing temporary TTS audio directory {temp_audio_dir}: {e}")
    
    if not video_url: # Should be caught earlier, but as a safeguard
        logger.error("Failed to generate video with HeyGen (final check). Workflow aborted.")
        return False

    # Step 2: Download video directly from HeyGen and upload to YouTube
    try:
        # Download video from HeyGen URL
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
        response = requests.get(video_url)
        if response.status_code == 200:
            with open(temp_file, "wb") as f:
                f.write(response.content)
            logger.info(f"Video downloaded from HeyGen to: {temp_file}")
            
            # Upload directly to YouTube
            description = metadata.get('description', '')
            tags = metadata.get('hashtags', [])
            
            video_id = upload_to_youtube(temp_file, title, description, tags)
            
            if video_id:
                logger.info("✅ YouTube upload successful!")
                logger.info(f"Video '{title}' is now available: https://www.youtube.com/watch?v={video_id}")
                return True
            else:
                logger.error("❌ YouTube upload failed.")
                return False
        else:
            logger.error(f"Failed to download video from HeyGen: {response.status_code}")
            return False
        
    finally:
        # Clean up temporary file
        if 'temp_file' in locals() and os.path.exists(temp_file):
            os.remove(temp_file)
            logger.info(f"Removed temporary video file: {temp_file}")

    return True

@exponential_backoff_retry()
def convert_numbers_to_words_in_script(client, script_data, model="claude-3-7-sonnet-20250219"):
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
        max_tokens=4000,  # Increased for longer single video scripts
        temperature=0.3,
        stream=True  # Enable streaming for reliability
    )
    
    # Just do basic stripping - final formatting will be done in optimize_heygen_script
    result = result.strip()
    
    return result

def convert_numbers_in_single_video(validated_data: Dict[str, Any], output_dir: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Convert all numbers to words in the single video script.
    
    Args:
        validated_data: Dictionary with validated script data
        output_dir: Directory to save output
        api_key: Anthropic API key (optional)
    
    Returns:
        Dictionary with paths to number-converted script files
    """
    logger.info("Step 5: Converting numbers to words in single video script")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Get Anthropic client
    client = create_claude_client(api_key)
    
    # Define output directory
    converted_dir = os.path.join(output_dir, "converted_script")
    
    # Create output directory path
    Path(converted_dir).mkdir(parents=True, exist_ok=True)
    
    # Create rate limiter to avoid hitting API limits
    rate_limiter = RateLimiter(calls_per_minute=10)
    
    script_data = validated_data.get('script_data', {})
    
    try:
        # Use rate limiter to prevent hitting API limits
        with rate_limiter:
            # Convert numbers to words
            logger.info("Converting numbers in single video script...")
            converted_script = convert_numbers_to_words_in_script(client, script_data)
        
        # Create output data
        converted_data = script_data.copy()
        
        # Save pre-conversion script
        converted_data['pre_conversion_script'] = script_data.get('heygen_script', '')
        
        # Update with converted script
        converted_data['heygen_script'] = converted_script
        
        # Save the converted data
        output_path = os.path.join(converted_dir, "converted_single_video_script.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=False, indent=2)
        
        # Also save as plain text for easy use with HeyGen
        title = script_data.get('title', '')
        heygen_path = os.path.join(converted_dir, "converted_single_video_script.txt")
        with open(heygen_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n{converted_script}")
        
        logger.info(f"Saved converted script to {output_path}")
        
        return {
            "converted_dir": converted_dir,
            "json_path": output_path,
            "text_path": heygen_path,
            "script_data": converted_data
        }
        
    except Exception as e:
        logger.error(f"Error converting numbers in script: {str(e)}")
        raise

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
        temperature=0.4,
        stream=True  # Enable streaming for reliability
    )
    
    # Final formatting fixes
    # Remove all newline characters for consistent spacing
    result = result.strip().replace('\n', '')
    
    # Fix 11labs compatibility issues - THIS IS THE FINAL FORMATTING FIX
    
    # 1. Replace escaped quotes in break tags with regular quotes
    result = re.sub(r'<break time=\\"([0-9.]+s)\\"/>', r'<break time="\1"/>', result)
    result = re.sub(r'<break time=\"([0-9.]+s)\"/>', r'<break time="\1"/>', result)
    
    # 2. Add additional break tags after CAM-2, CAM-3, and CAM-4 (not CAM-1)
    result = re.sub(r'(<!-- CAM‑([2-4]) -->)<speak>', r'\1<speak><break time="3s"/><break time="2s"/>', result)
    
    return result

def optimize_single_video_script(converted_data: Dict[str, Any], output_dir: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Optimize the single video script for natural delivery by HeyGen avatar.
    
    Args:
        converted_data: Dictionary with converted script data
        output_dir: Directory to save output
        api_key: Anthropic API key (optional)
    
    Returns:
        Dictionary with paths to optimized script files
    """
    logger.info("Step 6: HeyGen script optimization for single video")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Get Anthropic client
    client = create_claude_client(api_key)
    
    # Define output directory
    optimized_dir = os.path.join(output_dir, "optimized_script")
    
    # Create output directory path
    Path(optimized_dir).mkdir(parents=True, exist_ok=True)
    
    # Create rate limiter to avoid hitting API limits
    rate_limiter = RateLimiter(calls_per_minute=10)
    
    script_data = converted_data.get('script_data', {})
    script = script_data.get('heygen_script', '')
    title = script_data.get('title', '')
    
    try:
        # Use rate limiter to prevent hitting API limits
        with rate_limiter:
            # Optimize script for HeyGen
            logger.info("Optimizing script for HeyGen...")
            optimized_script = optimize_heygen_script(client, script)
        
        # Create a clean output with only necessary fields
        optimized_data = {
            'heygen_script': optimized_script,
            'title': title
        }
        
        # Copy other essential fields except scripts
        for key in ['hashtags', 'description']:
            if key in script_data:
                optimized_data[key] = script_data[key]
        
        # Save the optimized script metadata
        output_path = os.path.join(optimized_dir, "optimized_single_video_script.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(optimized_data, f, ensure_ascii=False, indent=2)
        
        # Also save as a plain text file for HeyGen
        heygen_path = os.path.join(optimized_dir, "optimized_single_video_script.txt")
        with open(heygen_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n{optimized_script}")
        
        logger.info(f"Saved optimized script to {output_path}")
        
        return {
            "optimized_dir": optimized_dir,
            "json_path": output_path,
            "text_path": heygen_path,
            "script_data": optimized_data
        }
        
    except Exception as e:
        logger.error(f"Error optimizing script: {str(e)}")
        raise

def validate_single_video_script(final_script_data: Dict[str, Any], output_dir: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Validate and fix the single video script to ensure it complies with HeyGen rules.
    
    Args:
        final_script_data: Dictionary with final script data
        output_dir: Directory to save output
        api_key: Anthropic API key (optional)
    
    Returns:
        Dictionary with paths to validated script files
    """
    logger.info("Step 4: Single video script validation")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Get Anthropic client
    client = create_claude_client(api_key)
    
    # Define output directory
    validated_dir = os.path.join(output_dir, "validated_script")
    
    # Create output directory path
    Path(validated_dir).mkdir(parents=True, exist_ok=True)
    
    # Create rate limiter to avoid hitting API limits
    rate_limiter = RateLimiter(calls_per_minute=10)
    
    script_data = final_script_data.get('script_data', {})
    
    try:
        # Use rate limiter to prevent hitting API limits
        with rate_limiter:
            # Validate and fix the script
            logger.info("Validating single video script...")
            # Format the prompt with top 10 hook examples
            hook_examples = "\n".join(HOOK_VARIATIONS[:10])
            user_prompt = SCRIPT_VALIDATION_PROMPT.format(
                hook_examples=hook_examples,
                title=script_data.get('title', ''),
                script=script_data.get('heygen_script', '')
            )
            
            validated_script = call_claude_api(
                client=client,
                model="claude-3-7-sonnet-20250219",
                prompt=user_prompt,
                system=SCRIPT_VALIDATION_SYSTEM_PROMPT,
                max_tokens=4000,  # Increased for longer single video scripts
                temperature=0.3,
                stream=True  # Enable streaming for reliability
            )
        
        # Create output data
        validated_data = script_data.copy()
        
        # Save original script before validation
        validated_data['pre_validation_script'] = script_data.get('heygen_script', '')
        
        # Update with validated script
        validated_data['heygen_script'] = validated_script.strip()
        
        # Save the validated data
        output_path = os.path.join(validated_dir, "validated_single_video_script.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(validated_data, f, ensure_ascii=False, indent=2)
        
        # Also save as plain text for easy use with HeyGen
        title = script_data.get('title', '')
        heygen_path = os.path.join(validated_dir, "validated_single_video_script.txt")
        with open(heygen_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n{validated_script}")
        
        logger.info(f"Saved validated script to {output_path}")
        
        return {
            "validated_dir": validated_dir,
            "json_path": output_path,
            "text_path": heygen_path,
            "script_data": validated_data
        }
        
    except Exception as e:
        logger.error(f"Error validating script: {str(e)}")
        raise 