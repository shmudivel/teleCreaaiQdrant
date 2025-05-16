import os
from pydub import AudioSegment
from pydub.silence import detect_silence

# Path to the audio file
input_file = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/tests/big_text_to_reels/elevenlabs_audio_4_способа_использовать_ИИ_о_которых_вы_не_дога.mp3"
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

# Load the audio file
print(f"Loading audio file: {input_file}")
audio = AudioSegment.from_mp3(input_file)

# Function to attempt cutting audio with a given threshold
def perform_cut_with_threshold(audio_segment, current_silence_thresh, min_sil_len, min_target_dur, max_target_dur, desired_cuts_count, buffer_ms):
    print(f"\\n--- Attempting with silence threshold: {current_silence_thresh} dBFS ---")
    print(f"Detecting silent parts (min_len: {min_sil_len}ms, thresh: {current_silence_thresh}dB)...")
    all_silent_parts_ms = detect_silence(
        audio_segment,
        min_silence_len=min_sil_len,
        silence_thresh=current_silence_thresh
    )

    all_silent_parts_sec = [(start / 1000, end / 1000) for start, end in all_silent_parts_ms]
    print(f"Found {len(all_silent_parts_sec)} raw silent parts based on initial detection:")
    if not all_silent_parts_sec:
        print("  No raw silences detected with current parameters.")
    else:
        for i, (start_sec, end_sec) in enumerate(all_silent_parts_sec):
            duration_sec = end_sec - start_sec
            print(f"  Raw Silence {i+1}: Start: {start_sec:.2f}s, End: {end_sec:.2f}s, Duration: {duration_sec:.2f}s")

    suitable_silences = []
    for start, end in all_silent_parts_sec:
        duration = end - start
        if min_target_dur <= duration <= max_target_dur:
            suitable_silences.append({'start': start, 'end': end, 'duration': duration})

    print(f"\\nFound {len(suitable_silences)} silences between {min_target_dur}s and {max_target_dur}s long:")
    for i, s in enumerate(suitable_silences):
        print(f"  Silence {i+1}: {s['start']:.2f}s - {s['end']:.2f}s (Duration: {s['duration']:.2f}s)")

    if len(suitable_silences) >= desired_cuts_count:
        print(f"\\nFound {len(suitable_silences)} suitable silences. Selecting {desired_cuts_count} for cutting...")
        suitable_silences.sort(key=lambda x: x['start'])
        
        cut_points_silences = []
        if len(suitable_silences) > desired_cuts_count:
            target_points_indices = [int(len(suitable_silences) * (i+1) / (desired_cuts_count + 1)) for i in range(desired_cuts_count)]
            if len(set(target_points_indices)) < desired_cuts_count :
                 print("Not enough spread in suitable silences to pick evenly, taking the first ones.")
                 cut_points_silences = suitable_silences[:desired_cuts_count]
            else:
                print(f"Attempting to pick {desired_cuts_count} silences spread out from available options.")
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
            print(f"Could not select {desired_cuts_count} cut points from {len(suitable_silences)} suitable silences. Aborting this attempt for threshold {current_silence_thresh}dB.")
            return []

        print("\\nSelected cut points (silences):")
        for i, s in enumerate(cut_points_silences):
            print(f"  Cut {i+1} will use silence: {s['start']:.2f}s - {s['end']:.2f}s (Duration: {s['duration']:.2f}s)")

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
                print(f"Warning: Segment {i+1} would be empty or have negative length. Fallback: cut at silence start.")
                safe_segment_end_ms = cut_timing['start_cut_at']
                if safe_segment_end_ms > last_cut_end_ms:
                    segments.append(audio_segment[last_cut_end_ms:safe_segment_end_ms])
                else:
                    print(f"Error: Could not create valid segment {i+1} for threshold {current_silence_thresh}dB. Skipping this cut point.")
            last_cut_end_ms = cut_timing['end_resume_at']
        segments.append(audio_segment[last_cut_end_ms:])
        
        segments = [s for s in segments if len(s) > 0] # Ensure no empty segments
        return segments

    elif len(suitable_silences) > 0:
        print(f"\\nFor threshold {current_silence_thresh}dB: Found {len(suitable_silences)} silences between {min_target_dur}s-{max_target_dur}s, but needed {desired_cuts_count} to make {desired_cuts_count+1} parts.")
        return []
    else:
        print(f"\\nFor threshold {current_silence_thresh}dB: No silences found between {min_target_dur}s and {max_target_dur}s.")
        print(f"  (min_silence_len: {min_sil_len}ms, actual_silence_thresh: {current_silence_thresh}dB used for this attempt)")
        return []

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
        num_desired_cuts, # Should be 3 for 4 parts
        end_of_word_buffer_ms
    )

    if len(segments_from_attempt) == num_desired_cuts + 1:
        print(f"\\nSuccessfully generated {len(segments_from_attempt)} parts with threshold {s_thresh_db} dBFS.")
        final_segments = segments_from_attempt
        achieved_target_parts = True
        final_threshold_used = s_thresh_db
        
        # Save segments
        print(f"\\nAudio will be split into {len(final_segments)} parts.")
        for i, segment in enumerate(final_segments):
            output_file_path = os.path.join(output_dir, f"part_{i + 1}.mp3")
            print(f"Saving part {i + 1} ({len(segment)/1000:.2f}s) to {output_file_path}")
            segment.export(output_file_path, format="mp3")
        
        print(f"\\nSuccessfully split audio into {len(final_segments)} parts using {num_desired_cuts} silences of {min_target_silence_duration}-{max_target_silence_duration}s (threshold: {final_threshold_used} dBFS).")
        break 
    else:
        print(f"Threshold {s_thresh_db} dBFS resulted in {len(segments_from_attempt)} parts. Needed {num_desired_cuts + 1} parts. Trying next threshold if available.")

if not achieved_target_parts:
    error_message = (
        f"Failed to generate {num_desired_cuts + 1} audio parts after trying thresholds: {threshold_levels_db}. "
        "Please check the audio file or adjust parameters like 'min_silence_len_param', "
        "'min_target_silence_duration', 'max_target_silence_duration', or 'num_desired_cuts'."
    )
    print(f"\\nERROR: {error_message}")
    raise ValueError(error_message)
