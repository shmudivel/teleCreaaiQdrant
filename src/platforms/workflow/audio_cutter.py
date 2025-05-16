import os
from pydub import AudioSegment
from pydub.silence import detect_silence
from typing import List, Optional
import logging

# Get a logger for this module
logger = logging.getLogger(__name__)

# Path to the audio file
input_file = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/tests/test_heygen_4_angles_api/ElevenLabs_2025-05-12T06_52_52_Тест_pvc_sp100_s50_sb75_se0_b_m2.mp3"
output_dir = os.path.dirname(input_file)

# --- Silence detection parameters ---
# To detect silences around 3-6 seconds, we can set:
# min_silence_len: slightly less than 3000ms to ensure we catch silences at the lower bound.
# silence_thresh: -40dB is a common starting point, can be adjusted if needed.
min_silence_len_param = 2200  # milliseconds (2.8 seconds)
# silence_thresh_param = -60    # dBFS - MADE EVEN STRICTER (was -44dB) # This will be controlled by the loop

# --- Target silence duration ---
min_target_silence_duration = 2.2  # seconds
max_target_silence_duration = 10.0  # seconds
num_desired_cuts = 3 # We want to find 3 silences to make 4 parts

# --- Buffer for end of words --- 
end_of_word_buffer_ms = 500 # milliseconds, give words a bit more room before cutting

def cut_audio_file(input_file: str, output_dir: str, 
                  min_silence_len_param: int = 2200,
                  min_target_silence_duration: float = 2.2,
                  max_target_silence_duration: float = 10.0,
                  num_desired_cuts: int = 3,
                  end_of_word_buffer_ms: int = 500) -> List[str]:
    """
    Cut an audio file into parts based on silences.
    
    Args:
        input_file: Path to the input MP3 file.
        output_dir: Directory to save the cut audio part_i.mp3 files.
        min_silence_len_param: Minimum length of silence in milliseconds to detect.
        min_target_silence_duration: Minimum duration of silence to consider for cutting (seconds).
        max_target_silence_duration: Maximum duration of silence to consider for cutting (seconds).
        num_desired_cuts: Number of cuts to make (resulting in num_desired_cuts+1 parts).
        end_of_word_buffer_ms: Buffer in milliseconds to avoid cutting words off.
        
    Returns:
        A list of paths to the generated audio part files, or an empty list if cutting failed.
    """
    # Load the audio file
    logger.info(f"Loading audio file: {input_file}")
    audio = AudioSegment.from_mp3(input_file)
    
    # Return value - generated file paths
    generated_part_paths = []
    
    # --- Main logic with iterative thresholds ---
    threshold_levels_db = [-60, -55, -50]
    achieved_target_parts = False
    final_segments = []
    final_threshold_used = None
    
    for s_thresh_db in threshold_levels_db:
        segments_from_attempt = perform_cut_with_threshold(
            audio,
            s_thresh_db,
            min_silence_len_param,
            min_target_silence_duration,
            max_target_silence_duration,
            num_desired_cuts,
            end_of_word_buffer_ms
        )

        if len(segments_from_attempt) == num_desired_cuts + 1:
            logger.info(f"Successfully generated {len(segments_from_attempt)} parts with threshold {s_thresh_db} dBFS.")
            final_segments = segments_from_attempt
            achieved_target_parts = True
            final_threshold_used = s_thresh_db
            
            # Save segments
            logger.info(f"Audio will be split into {len(final_segments)} parts.")
            for i, segment in enumerate(final_segments):
                output_file_path = os.path.join(output_dir, f"part_{i + 1}.mp3")
                logger.info(f"Saving part {i + 1} ({len(segment)/1000:.2f}s) to {output_file_path}")
                segment.export(output_file_path, format="mp3")
                generated_part_paths.append(output_file_path)
            
            logger.info(f"Successfully split audio into {len(final_segments)} parts using {num_desired_cuts} silences of {min_target_silence_duration}-{max_target_silence_duration}s (threshold: {final_threshold_used} dBFS).")
            break 
        else:
            logger.info(f"Threshold {s_thresh_db} dBFS resulted in {len(segments_from_attempt)} parts. Needed {num_desired_cuts + 1} parts. Trying next threshold if available.")

    if not achieved_target_parts:
        error_message = (
            f"Failed to generate {num_desired_cuts + 1} audio parts after trying thresholds: {threshold_levels_db}. "
            "Please check the audio file or adjust parameters like 'min_silence_len_param', "
            "'min_target_silence_duration', 'max_target_silence_duration', or 'num_desired_cuts'."
        )
        logger.error(f"ERROR: {error_message}")
        # Return empty list instead of raising error to be consistent with integration.py behavior
        return []
    
    return generated_part_paths

def perform_cut_with_threshold(audio_segment, current_silence_thresh, min_sil_len, min_target_dur, max_target_dur, desired_cuts_count, buffer_ms):
    logger.info(f"--- Attempting with silence threshold: {current_silence_thresh} dBFS ---")
    logger.info(f"Detecting silent parts (min_len: {min_sil_len}ms, thresh: {current_silence_thresh}dB)...")
    all_silent_parts_ms = detect_silence(
        audio_segment,
        min_silence_len=min_sil_len,
        silence_thresh=current_silence_thresh
    )

    all_silent_parts_sec = [(start / 1000, end / 1000) for start, end in all_silent_parts_ms]
    logger.info(f"Found {len(all_silent_parts_sec)} raw silent parts based on initial detection:")
    if not all_silent_parts_sec:
        logger.info("  No raw silences detected with current parameters.")
    else:
        for i, (start_sec, end_sec) in enumerate(all_silent_parts_sec):
            duration_sec = end_sec - start_sec
            logger.info(f"  Raw Silence {i+1}: Start: {start_sec:.2f}s, End: {end_sec:.2f}s, Duration: {duration_sec:.2f}s")

    suitable_silences = []
    for start, end in all_silent_parts_sec:
        duration = end - start
        if min_target_dur <= duration <= max_target_dur:
            suitable_silences.append({'start': start, 'end': end, 'duration': duration})

    logger.info(f"Found {len(suitable_silences)} silences between {min_target_dur}s and {max_target_dur}s long:")
    for i, s in enumerate(suitable_silences):
        logger.info(f"  Silence {i+1}: {s['start']:.2f}s - {s['end']:.2f}s (Duration: {s['duration']:.2f}s)")

    if len(suitable_silences) >= desired_cuts_count:
        logger.info(f"Found {len(suitable_silences)} suitable silences. Selecting {desired_cuts_count} for cutting...")
        suitable_silences.sort(key=lambda x: x['start'])
        
        cut_points_silences = []
        if len(suitable_silences) > desired_cuts_count:
            target_points_indices = [int(len(suitable_silences) * (i+1) / (desired_cuts_count + 1)) for i in range(desired_cuts_count)]
            if len(set(target_points_indices)) < desired_cuts_count :
                 logger.info("Not enough spread in suitable silences to pick evenly, taking the first ones.")
                 cut_points_silences = suitable_silences[:desired_cuts_count]
            else:
                logger.info(f"Attempting to pick {desired_cuts_count} silences spread out from available options.")
                temp_suitable_silences = list(suitable_silences)
                indices_to_pick = []
                if desired_cuts_count == 3 and len(temp_suitable_silences) >=3:
                     indices_to_pick = [0, len(temp_suitable_silences) // 2, len(temp_suitable_silences) -1]
                     if len(temp_suitable_silences) == 3: indices_to_pick = [0,1,2]
                     elif len(temp_suitable_silences) == 4: indices_to_pick = [0,1,2] 
                else: 
                     indices_to_pick = list(range(min(desired_cuts_count, len(temp_suitable_silences))))
                picked_silences_temp = [temp_suitable_silences[i] for i in sorted(list(set(indices_to_pick)))]
                cut_points_silences = picked_silences_temp[:desired_cuts_count]
        else: # len(suitable_silences) == desired_cuts_count
            cut_points_silences = suitable_silences
        
        cut_points_silences = cut_points_silences[:desired_cuts_count]

        if len(cut_points_silences) < desired_cuts_count:
            logger.info(f"Could not select {desired_cuts_count} cut points from {len(suitable_silences)} suitable silences. Aborting this attempt for threshold {current_silence_thresh}dB.")
            return []

        logger.info("Selected cut points (silences):")
        for i, s in enumerate(cut_points_silences):
            logger.info(f"  Cut {i+1} will use silence: {s['start']:.2f}s - {s['end']:.2f}s (Duration: {s['duration']:.2f}s)")

        cut_times_ms = []
        for s in cut_points_silences:
            cut_times_ms.append({'start_cut_at': int(s['start'] * 1000), 'end_resume_at': int(s['end'] * 1000)})

        segments = []
        last_cut_end_ms = 0
        for i, cut_timing in enumerate(cut_times_ms):
            potential_segment_end_ms = cut_timing['start_cut_at'] + buffer_ms
            actual_silence_end_ms = cut_timing['end_resume_at']
            segment_end_ms = min(potential_segment_end_ms, actual_silence_end_ms)
            if segment_end_ms > last_cut_end_ms:
                segments.append(audio_segment[last_cut_end_ms:segment_end_ms])
            else:
                logger.warning(f"Segment {i+1} would be empty or have negative length. Fallback: cut at silence start.")
                safe_segment_end_ms = cut_timing['start_cut_at']
                if safe_segment_end_ms > last_cut_end_ms:
                    segments.append(audio_segment[last_cut_end_ms:safe_segment_end_ms])
                else:
                    logger.error(f"Error: Could not create valid segment {i+1} for threshold {current_silence_thresh}dB. Skipping this cut point.")
            last_cut_end_ms = cut_timing['end_resume_at']
        segments.append(audio_segment[last_cut_end_ms:])
        
        segments = [s for s in segments if len(s) > 0] # Ensure no empty segments
        return segments

    elif len(suitable_silences) > 0:
        logger.info(f"For threshold {current_silence_thresh}dB: Found {len(suitable_silences)} silences between {min_target_dur}s-{max_target_dur}s, but needed {desired_cuts_count} to make {desired_cuts_count+1} parts.")
        return []
    else:
        logger.info(f"For threshold {current_silence_thresh}dB: No silences found between {min_target_dur}s and {max_target_dur}s.")
        logger.info(f"  (min_silence_len: {min_sil_len}ms, actual_silence_thresh: {current_silence_thresh}dB used for this attempt)")
        return []

# This block only runs when the script is executed directly (not when imported)
if __name__ == "__main__":
    # Setup basic logging for direct script execution
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Default parameters used when running as a script
    input_file = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/tests/test_heygen_4_angles_api/ElevenLabs_2025-05-12T06_52_52_Тест_pvc_sp100_s50_sb75_se0_b_m2.mp3"
    output_dir = os.path.dirname(input_file)
    min_silence_len_param = 2200  # milliseconds (2.8 seconds)
    min_target_silence_duration = 2.2  # seconds
    max_target_silence_duration = 10.0  # seconds
    num_desired_cuts = 3 # We want to find 3 silences to make 4 parts
    end_of_word_buffer_ms = 500 # milliseconds, give words a bit more room before cutting
    
    # Call the function with the default parameters
    cut_audio_file(
        input_file=input_file,
        output_dir=output_dir,
        min_silence_len_param=min_silence_len_param,
        min_target_silence_duration=min_target_silence_duration,
        max_target_silence_duration=max_target_silence_duration,
        num_desired_cuts=num_desired_cuts,
        end_of_word_buffer_ms=end_of_word_buffer_ms
    )
