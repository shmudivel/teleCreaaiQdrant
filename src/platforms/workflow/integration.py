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
from .analyze_google_doc import extract_doc_id_from_url, get_document_content, analyze_with_claude
from .create_reel_scripts import ReelGenerator
from .reel_picker import load_metadata_files, analyze_viral_potential, select_top_reels, save_top_reels, get_client
# Import prompts
from .prompts import (
    DEFAULT_EDIT_GUIDELINES, HOOK_VARIATIONS, CALL_TO_ACTION_VARIATIONS,
    FINAL_EDITING_PROMPT, FINAL_EDITING_SYSTEM_PROMPT,
    HEYGEN_OPTIMIZATION_PROMPT, HEYGEN_OPTIMIZATION_SYSTEM_PROMPT,
    SCRIPT_VALIDATION_PROMPT, SCRIPT_VALIDATION_SYSTEM_PROMPT,
    NUMBER_CONVERSION_PROMPT, NUMBER_CONVERSION_SYSTEM_PROMPT
)
# Import API utilities
from .api_utils import call_claude_api, RateLimiter, exponential_backoff_retry, create_claude_client

# +++ Imports for audio cutting +++
from pydub import AudioSegment
from pydub.silence import detect_silence
# Import the audio_cutter module
from .audio_cutter import cut_audio_file
# +++ End imports for audio cutting +++

# +++ Imports for HeyGen video generation from the dedicated script +++
from .generate_heygen_video import upload_audio_file, generate_video_with_multiple_avatars, check_video_status
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

def process_google_doc(url: str, service_account_file: str) -> str:
    """Process a Google Doc and divide it into sections.
    
    Args:
        url: Google Doc URL
        service_account_file: Path to service account JSON file
    
    Returns:
        Path to the created analyzed text file
    """
    logger.info("Step 1: Analyzing Google Doc")
    logger.info(f"Extracting content from: {url}")
    
    # Extract document ID from URL
    doc_id = extract_doc_id_from_url(url)
    logger.info(f"Document ID: {doc_id}")
    
    # Get document content
    content = get_document_content(doc_id, service_account_file)
    logger.info(f"Retrieved {len(content)} characters from the document")
    
    # Analyze with Claude
    logger.info("Analyzing content with Claude...")
    analyzed_text = analyze_with_claude(content)
    
    # Create output file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(script_dir, f"analyzed_doc_{timestamp}.txt")
    
    # Write the analyzed text to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(analyzed_text)
    
    logger.info(f"Analysis written to {output_file}")
    return output_file

def create_reel_scripts(input_file: str, output_dir: str, 
                       overlap: int = 2, workers: int = 4, 
                       sections: Optional[str] = None, count: Optional[int] = None,
                       api_key: Optional[str] = None) -> str:
    """Create reel scripts from analyzed text file.
    
    Args:
        input_file: Path to analyzed text file
        output_dir: Directory to save output
        overlap: Number of paragraphs to include from adjacent sections
        workers: Maximum number of parallel workers
        sections: Specific section numbers to process (comma-separated)
        count: Number of reels to generate, starting from the beginning
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the metadata directory
    """
    logger.info("Step 2: Generating reel scripts")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Create generator
    generator = ReelGenerator(
        api_key=api_key,
        output_dir=output_dir,
        overlap_paragraphs=overlap
    )
    
    metadata_dir = os.path.join(output_dir, "metadata")
    
    # Process specific sections if requested
    if sections:
        section_numbers = [int(s.strip()) for s in sections.split(',')]
        
        # Read and parse the text
        text = generator.read_analyzed_text(input_file)
        
        # Split into sections
        sections_list = generator.split_into_sections(text)
        logger.info(f"Split text into {len(sections_list)} sections")
        
        # Extract titles and add context
        titled_sections = generator.extract_section_titles(sections_list)
        all_enriched_sections = generator.add_context_to_sections(titled_sections)
        
        # Filter sections by selected numbers
        enriched_sections = [s for s in all_enriched_sections if s['id'] in section_numbers]
        
        if not enriched_sections:
            logger.error(f"No valid sections found with numbers: {section_numbers}")
            return metadata_dir
            
        logger.info(f"Processing {len(enriched_sections)} selected sections: {section_numbers}")
        
        # Process selected sections in parallel
        processed_sections = generator.process_sections_parallel(enriched_sections, workers)
        
        # Save results
        generator.save_reel_scripts(processed_sections)
        
    elif count:
        # Read and parse the text
        text = generator.read_analyzed_text(input_file)
        
        # Split into sections
        sections_list = generator.split_into_sections(text)
        logger.info(f"Split text into {len(sections_list)} sections")
        
        # Extract titles and add context
        titled_sections = generator.extract_section_titles(sections_list)
        all_enriched_sections = generator.add_context_to_sections(titled_sections)
        
        # Take first N sections
        count = min(count, len(all_enriched_sections))
        enriched_sections = all_enriched_sections[:count]
        
        logger.info(f"Processing first {count} sections")
        
        # Process selected sections in parallel
        processed_sections = generator.process_sections_parallel(enriched_sections, workers)
        
        # Save results
        generator.save_reel_scripts(processed_sections)
    else:
        # Process all sections
        generator.process_file(
            input_filepath=input_file,
            max_workers=workers
        )
    
    logger.info(f"Reel scripts generated and saved to {output_dir}")
    return metadata_dir

def pick_top_reels(metadata_dir: str, top_n: int = 7, api_key: Optional[str] = None) -> str:
    """Select top reels based on viral potential.
    
    Args:
        metadata_dir: Directory containing metadata files
        top_n: Number of top reels to select
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the top reels directory
    """
    logger.info("Step 3: Picking top reels")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Define output directory
    parent_dir = os.path.dirname(metadata_dir)
    top_reels_dir = os.path.join(parent_dir, "top_reels")
    
    # Create output directory path
    Path(top_reels_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading metadata files from {metadata_dir}...")
    metadata_files = load_metadata_files(metadata_dir)
    logger.info(f"Loaded {len(metadata_files)} metadata files.")
    
    logger.info("Analyzing viral potential with Claude API...")
    # Need to set this temporarily because the module is imported
    os.environ["ANTHROPIC_API_KEY"] = api_key
    analyzed_reels = analyze_viral_potential(metadata_files, api_key)
    
    logger.info(f"Selecting top {top_n} viral reels...")
    top_reels = select_top_reels(analyzed_reels, top_n=top_n)
    
    logger.info(f"Saving top reels to {top_reels_dir}...")
    save_top_reels(top_reels, metadata_dir, top_reels_dir)
    
    logger.info("Top reels saved successfully")
    
    # Print summary of top reels
    logger.info("\nTop Viral Reels Summary:")
    for i, reel in enumerate(top_reels, 1):
        score = reel.get('viral_analysis', {}).get('score', 'N/A')
        title = reel.get('title', 'No title')
        filename = reel.get('filename', 'Unknown file')
        logger.info(f"{i}. {filename} - {title} (Score: {score})")
    
    return top_reels_dir

@exponential_backoff_retry()
def edit_reel_script(client, reel_data, edit_prompt, hook_variant, call_to_action_variant, model="claude-3-7-sonnet-20250219"):
    """Edit a reel script with retry logic."""
    script = reel_data.get('heygen_script', '')
    title = reel_data.get('title', '')
    
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
        max_tokens=1500,
        temperature=0.7
    )
    
    return result.strip()

def final_reel_editing(top_reels_dir: str, edit_prompt: str, api_key: Optional[str] = None) -> str:
    """Apply final edits to top reels to improve engagement.
    
    Args:
        top_reels_dir: Directory containing top reels
        edit_prompt: Instructions for editing the reels
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the final reels directory
    """
    logger.info("Step 4: Final reel editing")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Get Anthropic client
    client = create_claude_client(api_key)
    
    # Define output directory
    parent_dir = os.path.dirname(top_reels_dir)
    final_reels_dir = os.path.join(parent_dir, "final_reels")
    
    # Create output directory path
    Path(final_reels_dir).mkdir(parents=True, exist_ok=True)
    
    # Create rate limiter to avoid hitting API limits
    rate_limiter = RateLimiter(calls_per_minute=10)
    
    # Load metadata files
    logger.info(f"Loading top reels from {top_reels_dir}...")
    metadata_files = []
    for filename in os.listdir(top_reels_dir):
        if filename.endswith('.json') and not filename.startswith('analysis_'):
            file_path = os.path.join(top_reels_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    metadata_files.append(data)
                    logger.info(f"Loaded {filename}")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    
    for i, reel_data in enumerate(metadata_files):
        # Select a random hook variant for each reel
        hook_variant = random.choice(HOOK_VARIATIONS)
        
        # Select a random call to action variant
        call_to_action_variant = random.choice(CALL_TO_ACTION_VARIATIONS)
        
        try:
            # Use rate limiter to prevent hitting API limits
            with rate_limiter:
                # Call Claude to edit the script
                logger.info(f"Editing reel {i+1}/{len(metadata_files)}...")
                edited_script = edit_reel_script(client, reel_data, edit_prompt, hook_variant, call_to_action_variant)
            
            # Update the reel data
            reel_data['original_script'] = reel_data.get('heygen_script', '')
            reel_data['heygen_script'] = edited_script
            reel_data['hook_variant'] = hook_variant
            reel_data['call_to_action_variant'] = call_to_action_variant
            
            # Save the edited reel metadata
            output_path = os.path.join(final_reels_dir, f"final_{i+1:02d}_{os.path.basename(reel_data.get('filename', f'reel_{i+1}.json'))}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(reel_data, f, ensure_ascii=False, indent=2)
            
            # Also save as a plain text file for heygen
            title = reel_data.get('title', '')
            heygen_filename = f"final_heygen_{i+1:02d}.txt"
            heygen_path = os.path.join(final_reels_dir, heygen_filename)
            with open(heygen_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n{edited_script}")
            
            logger.info(f"Saved edited reel to {output_path}")
            
        except Exception as e:
            logger.error(f"Error editing reel {i+1}: {str(e)}")
    
    logger.info(f"Final reel editing completed. Edited reels saved to: {final_reels_dir}")
    return final_reels_dir

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

        # Step 1b: Upload audio to HeyGen
        logger.info(f"Uploading generated audio '{audio_file_path_for_tts}' to HeyGen.")
        audio_asset_id = upload_audio_file(HEYGEN_API_KEY, audio_file_path_for_tts)

        if not audio_asset_id:
            logger.error(f"Failed to upload audio asset to HeyGen for '{title}'.")
            return False

        # Step 1c: Generate HeyGen video using the audio asset
        logger.info(f"Generating HeyGen video for '{title}' using audio asset ID '{audio_asset_id}'.")
        # Using HEYGEN_AVATAR_ID_1 as a default for single script/scene videos
        video_id_response = generate_video_with_multiple_avatars(
            HEYGEN_API_KEY,
            avatar_ids=[HEYGEN_AVATAR_ID_1], # Needs a list of avatar IDs
            audio_asset_ids=[audio_asset_id]  # Needs a list of audio asset IDs
        )
        
        # generate_video_with_multiple_avatars returns video_id directly, not a dict
        video_id = video_id_response 

        if not video_id:
            logger.error(f"Failed to start HeyGen video generation for '{title}'.")
            return False
        
        logger.info(f"HeyGen video generation started for '{title}'. Video ID: {video_id}")

        # Step 1d: Check video status
        video_url = check_video_status(HEYGEN_API_KEY, video_id)
        
        if not video_url:
            logger.error(f"HeyGen video generation failed or did not complete for '{title}'.")
            return False

    except Exception as e:
        logger.error(f"Error during HeyGen video generation pipeline for '{title}': {e}")
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

    # Step 2: Upload to Google Drive
    title = metadata.get('title', 'HeyGen Generated Video')
    file_name = f"{title.replace(' ', '_')[:30]}_video.mp4"  # Limit filename length
    drive_info = upload_to_drive(video_url, file_name, title)
    if not drive_info:
        logger.error("Failed to upload to Google Drive. Workflow aborted.")
        return False
    
    file_id = drive_info['file_id']
    temp_video_path = drive_info['temp_path']
    
    try:
        # Step 3: Download from Google Drive for YouTube upload
        temp_video_path = download_from_drive(file_id)
        
        # Step 4: Upload to YouTube
        description = metadata.get('description', '')
        tags = metadata.get('hashtags', [])
        
        try:
            logger.info(f"Attempting to upload video to YouTube: {title}")
            video_id = upload_to_youtube(temp_video_path, title, description, tags)
            
            if video_id:
                logger.info("✅ YouTube upload successful!")
                logger.info(f"Video '{title}' is now available on YouTube: https://www.youtube.com/watch?v={video_id}")
                return True
            else:
                logger.error("❌ YouTube upload failed. Check logs for details.")
                return False
        except RuntimeError as e:
            # Handle the specific error about browser authentication
            if "OAuth authentication requires a browser" in str(e):
                logger.error("❌ YouTube upload failed: Authentication error")
                logger.error("To fix this issue:")
                logger.error("1. Run the YouTube authentication on a local machine with a browser")
                logger.error("2. Copy the resulting youtube_token.json file to one of these locations:")
                logger.error("   - /app/youtube_token.json (Docker container)")
                logger.error("   - The application root directory")
                logger.error("   - Set YOUTUBE_TOKEN_PATH environment variable")
                logger.error(f"Detailed error: {str(e)}")
                return False
            else:
                # Re-raise other runtime errors
                raise
        except Exception as e:
            logger.error(f"❌ YouTube upload failed: {str(e)}")
            return False
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            logger.info(f"Removed temporary video file: {temp_video_path}")

    return converted_dir

@exponential_backoff_retry()
def convert_numbers_to_words(client, script_data, model="claude-3-7-sonnet-20250219"):
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
        max_tokens=2000,
        temperature=0.3
    )
    
    # Just do basic stripping - final formatting will be done in optimize_heygen_script
    result = result.strip()
    
    return result

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
        temperature=0.4
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

def optimize_heygen_scripts(final_reels_dir: str, api_key: Optional[str] = None) -> str:
    """Optimize scripts for natural delivery by HeyGen avatar.
    
    Args:
        final_reels_dir: Directory containing edited reel scripts
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the directory with optimized scripts
    """
    logger.info("Step 7: HeyGen script optimization")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Get Anthropic client
    client = create_claude_client(api_key)
    
    # Define output directory
    parent_dir = os.path.dirname(final_reels_dir)
    optimized_dir = os.path.join(parent_dir, "optimized_scripts")
    
    # Create output directory path
    Path(optimized_dir).mkdir(parents=True, exist_ok=True)
    
    # Create rate limiter to avoid hitting API limits
    rate_limiter = RateLimiter(calls_per_minute=10)
    
    # Load reel data
    logger.info(f"Loading scripts from {final_reels_dir}...")
    reels_data = []
    for filename in os.listdir(final_reels_dir):
        # Modified to handle different prefixes (final_, validated_, or converted_)
        if filename.endswith('.json') and (filename.startswith('final_') or 
                                         filename.startswith('validated_') or 
                                         filename.startswith('converted_')):
            file_path = os.path.join(final_reels_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reels_data.append({
                        'data': data,
                        'filename': filename
                    })
                    logger.info(f"Loaded {filename}")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    
    for i, reel_item in enumerate(reels_data):
        reel_data = reel_item['data']
        script = reel_data.get('heygen_script', '')
        title = reel_data.get('title', '')
        
        try:
            # Use rate limiter to prevent hitting API limits
            with rate_limiter:
                # Optimize script for HeyGen
                logger.info(f"Optimizing script {i+1}/{len(reels_data)} for HeyGen...")
                optimized_script = optimize_heygen_script(client, script)
            
            # Create a clean output with only necessary fields
            optimized_data = {
                'heygen_script': optimized_script,
                'title': title
            }
            
            # Copy other essential fields except scripts
            for key in ['hashtags', 'description']:
                if key in reel_data:
                    optimized_data[key] = reel_data[key]
            
            # Determine output filename
            if reel_item['filename'].startswith('final_'):
                base_name = os.path.basename(reel_item['filename'])
            elif reel_item['filename'].startswith('validated_'):
                base_name = os.path.basename(reel_item['filename']).replace('validated_', '')
            else:  # converted_
                base_name = os.path.basename(reel_item['filename']).replace('converted_', '')
                
            # Save the optimized reel metadata
            output_path = os.path.join(optimized_dir, f"optimized_{base_name}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(optimized_data, f, ensure_ascii=False, indent=2)
            
            # Also save as a plain text file for HeyGen
            heygen_filename = f"optimized_heygen_{i+1:02d}.txt"
            heygen_path = os.path.join(optimized_dir, heygen_filename)
            with open(heygen_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n{optimized_script}")
            
            logger.info(f"Saved optimized script to {output_path}")
            
        except Exception as e:
            logger.error(f"Error optimizing script {i+1}: {str(e)}")
    
    logger.info(f"Script optimization completed. Optimized scripts saved to: {optimized_dir}")
    return optimized_dir

@exponential_backoff_retry()
def validate_heygen_script(client, script_data, model="claude-3-7-sonnet-20250219"):
    """Validate and fix a HeyGen script if it doesn't comply with rules.
    
    Args:
        client: Anthropic client
        script_data: Dictionary containing script data ('heygen_script', 'title')
        model: Claude model to use
        
    Returns:
        Fixed script that complies with HeyGen rules
    """
    script = script_data.get('heygen_script', '')
    title = script_data.get('title', '')
    
    # Format the prompt with top 10 hook examples
    hook_examples = "\n".join(HOOK_VARIATIONS[:10])
    user_prompt = SCRIPT_VALIDATION_PROMPT.format(
        hook_examples=hook_examples,
        title=title,
        script=script
    )
    
    result = call_claude_api(
        client=client,
        model=model,
        prompt=user_prompt,
        system=SCRIPT_VALIDATION_SYSTEM_PROMPT,
        max_tokens=2000,
        temperature=0.3
    )
    
    return result.strip()

def validate_heygen_scripts(optimized_dir: str, api_key: Optional[str] = None) -> str:
    """Validate and fix optimized scripts to ensure they comply with HeyGen rules.
    
    Args:
        optimized_dir: Directory containing optimized scripts
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the directory with validated scripts
    """
    logger.info("Step 6: HeyGen script validation and fixing")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Get Anthropic client
    client = create_claude_client(api_key)
    
    # Define output directory
    parent_dir = os.path.dirname(optimized_dir)
    validated_dir = os.path.join(parent_dir, "validated_scripts")
    
    # Create output directory path
    Path(validated_dir).mkdir(parents=True, exist_ok=True)
    
    # Create rate limiter to avoid hitting API limits
    rate_limiter = RateLimiter(calls_per_minute=10)
    
    # Load optimized reel data
    logger.info(f"Loading scripts from {optimized_dir}...")
    reels_data = []
    for filename in os.listdir(optimized_dir):
        # Modified to handle both "optimized_" and "final_" prefixes
        if filename.endswith('.json') and (filename.startswith('optimized_') or filename.startswith('final_')):
            file_path = os.path.join(optimized_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reels_data.append({
                        'data': data,
                        'filename': filename
                    })
                    logger.info(f"Loaded {filename}")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    
    for i, reel_item in enumerate(reels_data):
        reel_data = reel_item['data']
        
        try:
            # Use rate limiter to prevent hitting API limits
            with rate_limiter:
                # Validate and fix the script
                logger.info(f"Validating script {i+1}/{len(reels_data)}...")
                validated_script = validate_heygen_script(client, reel_data)
            
            # Create output data
            validated_data = reel_data.copy()
            
            # Save original script before validation
            validated_data['pre_validation_script'] = reel_data.get('heygen_script', '')
            
            # Update with validated script
            validated_data['heygen_script'] = validated_script
            
            # Determine output filename
            if reel_item['filename'].startswith('optimized_'):
                output_filename = f"validated_{os.path.basename(reel_item['filename']).replace('optimized_', '')}"
            else:
                output_filename = f"validated_{os.path.basename(reel_item['filename']).replace('final_', '')}"
            
            # Save the validated data
            output_path = os.path.join(validated_dir, output_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(validated_data, f, ensure_ascii=False, indent=2)
            
            # Also save as plain text for easy use with HeyGen
            title = reel_data.get('title', '')
            heygen_filename = f"validated_heygen_{i+1:02d}.txt"
            heygen_path = os.path.join(validated_dir, heygen_filename)
            with open(heygen_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n{validated_script}")
            
            logger.info(f"Saved validated script to {output_path}")
            
        except Exception as e:
            logger.error(f"Error validating script {i+1}: {str(e)}")
    
    logger.info(f"Script validation completed. Validated scripts saved to: {validated_dir}")
    return validated_dir

def convert_all_numbers_to_words(validated_dir: str, api_key: Optional[str] = None) -> str:
    """Convert all numbers to words in validated scripts.
    
    Args:
        validated_dir: Directory containing validated scripts
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the directory with number-converted scripts
    """
    logger.info("Step 6: Converting numbers to words in scripts")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Get Anthropic client
    client = create_claude_client(api_key)
    
    # Define output directory
    parent_dir = os.path.dirname(validated_dir)
    converted_dir = os.path.join(parent_dir, "converted_scripts")
    
    # Create output directory path
    Path(converted_dir).mkdir(parents=True, exist_ok=True)
    
    # Create rate limiter to avoid hitting API limits
    rate_limiter = RateLimiter(calls_per_minute=10)
    
    # Load validated reel data
    logger.info(f"Loading scripts from {validated_dir}...")
    reels_data = []
    for filename in os.listdir(validated_dir):
        # Modified to handle files with validated_ and other prefixes
        if filename.endswith('.json'):
            file_path = os.path.join(validated_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reels_data.append({
                        'data': data,
                        'filename': filename
                    })
                    logger.info(f"Loaded {filename}")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    
    for i, reel_item in enumerate(reels_data):
        reel_data = reel_item['data']
        
        try:
            # Use rate limiter to prevent hitting API limits
            with rate_limiter:
                # Convert numbers to words
                logger.info(f"Converting numbers in script {i+1}/{len(reels_data)}...")
                converted_script = convert_numbers_to_words(client, reel_data)
            
            # Create output data
            converted_data = reel_data.copy()
            
            # Save pre-conversion script
            converted_data['pre_conversion_script'] = reel_data.get('heygen_script', '')
            
            # Update with converted script
            converted_data['heygen_script'] = converted_script
            
            # Determine the output filename based on the input filename
            if reel_item['filename'].startswith('validated_'):
                output_filename = f"converted_{os.path.basename(reel_item['filename']).replace('validated_', '')}"
            else:
                # If not a validated_ file, preserve the original name with converted_ prefix
                output_filename = f"converted_{os.path.basename(reel_item['filename'])}"
            
            # Save the converted data
            output_path = os.path.join(converted_dir, output_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(converted_data, f, ensure_ascii=False, indent=2)
            
            # Also save as plain text for easy use with HeyGen
            title = reel_data.get('title', '')
            heygen_filename = f"converted_heygen_{i+1:02d}.txt"
            heygen_path = os.path.join(converted_dir, heygen_filename)
            with open(heygen_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n{converted_script}")
            
            logger.info(f"Saved converted script to {output_path}")
            
        except Exception as e:
            logger.error(f"Error converting numbers in script {i+1}: {str(e)}")
    
    logger.info(f"Number conversion completed. Converted scripts saved to: {converted_dir}")
    return converted_dir

def process_google_doc_to_reels(doc_url: str, output_dir: Optional[str] = None, top_n: int = 7) -> Dict[str, str]:
    """Process a Google Doc and convert it to reels.
    
    This is the main function that combines all the steps of the workflow.
    
    Args:
        doc_url: URL of the Google Doc to process
        output_dir: Directory to save output files (optional)
        top_n: Number of top reels to select (default: 7)
        
    Returns:
        Dictionary with paths to generated content
    """
    # Use edit guidelines from prompts.py
    edit_prompt = DEFAULT_EDIT_GUIDELINES
    
    # Create output directory if not provided
    if not output_dir:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"output_{timestamp}"
        
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Step 1: Process Google Doc
        analyzed_doc_path = process_google_doc(doc_url, SERVICE_ACCOUNT_PATH)
        
        # Step 2: Generate reel scripts
        metadata_dir = create_reel_scripts(
            input_file=analyzed_doc_path,
            output_dir=output_dir,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 3: Pick top reels
        top_reels_dir = pick_top_reels(
            metadata_dir=metadata_dir,
            top_n=top_n,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 4: Final reel editing
        final_reels_dir = final_reel_editing(
            top_reels_dir=top_reels_dir,
            edit_prompt=edit_prompt,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 5: Validate and fix scripts
        validated_dir = validate_heygen_scripts(
            optimized_dir=final_reels_dir,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 6: Convert numbers to words
        converted_dir = convert_all_numbers_to_words(
            validated_dir=validated_dir,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Step 7: Optimize scripts for HeyGen (now the last step)
        optimized_dir = optimize_heygen_scripts(
            final_reels_dir=converted_dir,
            api_key=ANTHROPIC_API_KEY
        )
        
        # Return paths to various directories for reference
        return {
            "analyzed_doc": analyzed_doc_path,
            "metadata_dir": metadata_dir,
            "top_reels_dir": top_reels_dir,
            "final_reels_dir": final_reels_dir,
            "validated_dir": validated_dir,
            "converted_dir": converted_dir,
            "optimized_dir": optimized_dir
        }
    
    except Exception as e:
        logger.error(f"An error occurred in the workflow: {str(e)}")
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