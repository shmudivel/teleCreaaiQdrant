import os
from pydub import AudioSegment
from pydub.silence import detect_silence

# Path to the audio file
input_file = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/tests/test_heygen_4_angles_api/ElevenLabs_2025-05-12T06_52_52_Тест_pvc_sp100_s50_sb75_se0_b_m2.mp3"
output_dir = os.path.dirname(input_file)

# --- Silence detection parameters ---
# To detect silences around 3-6 seconds, we can set:
# min_silence_len: slightly less than 3000ms to ensure we catch silences at the lower bound.
# silence_thresh: -40dB is a common starting point, can be adjusted if needed.
min_silence_len_param = 2800  # milliseconds (2.8 seconds)
silence_thresh_param = -46    # dBFS - MADE EVEN STRICTER (was -44dB)

# --- Target silence duration ---
min_target_silence_duration = 3.0  # seconds
max_target_silence_duration = 6.0  # seconds
num_desired_cuts = 3 # We want to find 3 silences to make 4 parts

# --- Buffer for end of words --- 
end_of_word_buffer_ms = 700 # milliseconds, give words a bit more room before cutting

# Load the audio file
print(f"Loading audio file: {input_file}")
audio = AudioSegment.from_mp3(input_file)

# Detect silent parts
print(f"Detecting silent parts (min_len: {min_silence_len_param}ms, thresh: {silence_thresh_param}dB)...")
all_silent_parts_ms = detect_silence( # Renamed to all_silent_parts_ms for clarity
    audio,
    min_silence_len=min_silence_len_param,
    silence_thresh=silence_thresh_param
)

# Convert silent parts from ms to seconds for easier handling
all_silent_parts_sec = [(start / 1000, end / 1000) for start, end in all_silent_parts_ms]
print(f"Found {len(all_silent_parts_sec)} raw silent parts based on initial detection:")
# --- New diagnostic print ---
if not all_silent_parts_sec:
    print("  No raw silences detected with current parameters.")
else:
    for i, (start_sec, end_sec) in enumerate(all_silent_parts_sec):
        duration_sec = end_sec - start_sec
        print(f"  Raw Silence {i+1}: Start: {start_sec:.2f}s, End: {end_sec:.2f}s, Duration: {duration_sec:.2f}s")
# --- End of new diagnostic print ---

# Filter for silences within the target duration (3-6 seconds)
suitable_silences = []
for start, end in all_silent_parts_sec:
    duration = end - start
    if min_target_silence_duration <= duration <= max_target_silence_duration:
        suitable_silences.append({'start': start, 'end': end, 'duration': duration})

print(f"\nFound {len(suitable_silences)} silences between {min_target_silence_duration}s and {max_target_silence_duration}s long:")
for i, s in enumerate(suitable_silences):
    print(f"  Silence {i+1}: {s['start']:.2f}s - {s['end']:.2f}s (Duration: {s['duration']:.2f}s)")

# Proceed if we found enough suitable silences
if len(suitable_silences) >= num_desired_cuts:
    print(f"\nFound {len(suitable_silences)} suitable silences. Selecting {num_desired_cuts} for cutting...")

    # If we have more than num_desired_cuts, we might want to pick the "best" ones.
    # For now, let's sort by duration (longest first) and pick the top ones,
    # or sort by start time if we prefer to pick them sequentially.
    # The original script tried to pick silences that divide the audio evenly. Let's adapt that.

    # Sort by start time to process them in order
    suitable_silences.sort(key=lambda x: x['start'])

    total_duration_audio = len(audio) / 1000  # total duration in seconds
    
    # If we have exactly num_desired_cuts or a few more, we can select them strategically.
    # For simplicity, if we have more, we'll pick the first 'num_desired_cuts'.
    # A more sophisticated approach would be to use the 'target_points' logic
    # from your original script if there are many choices.
    
    if len(suitable_silences) > num_desired_cuts:
        # Option 1: Pick the first N
        # cut_points_silences = suitable_silences[:num_desired_cuts]
        
        # Option 2: Try to pick evenly spaced ones (adapted from original)
        target_points_indices = [int(len(suitable_silences) * (i+1) / (num_desired_cuts + 1)) for i in range(num_desired_cuts)]
        if len(set(target_points_indices)) < num_desired_cuts : # if indices are not unique (not enough spread)
             print("Not enough spread in suitable silences to pick evenly, taking the first ones.")
             cut_points_silences = suitable_silences[:num_desired_cuts]
        else:
            print(f"Attempting to pick {num_desired_cuts} silences spread out from available options.")
            temp_suitable_silences = list(suitable_silences) # Make a copy to remove items
            cut_points_silences = []

            # Simplified selection: pick N silences that are somewhat spread out
            # This example picks the first, middle-ish, and last-ish available if many
            indices_to_pick = []
            if num_desired_cuts == 3 and len(temp_suitable_silences) >=3:
                 indices_to_pick = [0, len(temp_suitable_silences) // 2, len(temp_suitable_silences) -1]
                 # Ensure unique indices if len is small
                 if len(temp_suitable_silences) == 3: indices_to_pick = [0,1,2]
                 elif len(temp_suitable_silences) == 4: indices_to_pick = [0,1,2] # or [0,1,3] or [0,2,3]
            else: # default to first N
                 indices_to_pick = list(range(min(num_desired_cuts, len(temp_suitable_silences))))

            picked_silences_temp = [temp_suitable_silences[i] for i in sorted(list(set(indices_to_pick)))]
            cut_points_silences = picked_silences_temp[:num_desired_cuts]


    else: # len(suitable_silences) == num_desired_cuts
        cut_points_silences = suitable_silences
    
    # Ensure we only have num_desired_cuts
    cut_points_silences = cut_points_silences[:num_desired_cuts]


    print("\nSelected cut points (silences):")
    for i, s in enumerate(cut_points_silences):
        print(f"  Cut {i+1} will use silence: {s['start']:.2f}s - {s['end']:.2f}s (Duration: {s['duration']:.2f}s)")

    # Convert selected silences start/end times back to milliseconds for pydub
    # We cut AT the silence, so the segment ends at silence_start, and the next starts at silence_end.
    cut_times_ms = []
    for s in cut_points_silences:
        cut_times_ms.append({'start_cut_at': int(s['start'] * 1000), 'end_resume_at': int(s['end'] * 1000)})

    # Create the segments
    segments = []
    last_cut_end_ms = 0

    for i, cut_timing in enumerate(cut_times_ms):
        # Original segment end: cut_timing['start_cut_at'] (start of detected silence)
        # New segment end: cut_timing['start_cut_at'] + end_of_word_buffer_ms
        # Ensure this new end does not exceed the actual end of the detected silence (or even get too close to it)
        # and also does not exceed the total audio length (though less likely here)
        
        potential_segment_end_ms = cut_timing['start_cut_at'] + end_of_word_buffer_ms
        actual_silence_end_ms = cut_timing['end_resume_at']
        
        # Ensure the buffered cut doesn't go beyond the detected silence's end
        # or a minimum remaining silence duration if desired (e.g., keep 100ms of silence)
        # For now, just ensure it doesn't exceed the silence end.
        segment_end_ms = min(potential_segment_end_ms, actual_silence_end_ms)
        
        # Ensure segment_end_ms is greater than last_cut_end_ms to avoid empty/negative segments
        if segment_end_ms > last_cut_end_ms:
            segments.append(audio[last_cut_end_ms:segment_end_ms])
        else:
            print(f"Warning: Segment {i+1} would be empty or have negative length due to buffer. Start: {last_cut_end_ms}, Potential End: {segment_end_ms}. Trying cut at silence start.")
            # Fallback: cut at the very start of the silence if buffer causes issues
            safe_segment_end_ms = cut_timing['start_cut_at']
            if safe_segment_end_ms > last_cut_end_ms:
                segments.append(audio[last_cut_end_ms:safe_segment_end_ms])
            else:
                print(f"Error: Could not create valid segment {i+1}. Skipping.")

        last_cut_end_ms = cut_timing['end_resume_at'] # Next segment starts after the full detected silence

    # Add the final segment (from the end of the last silence to the end of the audio)
    # Ensure last_cut_end_ms is not beyond audio length (pydub handles slicing past end gracefully by returning up to end)
    segments.append(audio[last_cut_end_ms:])

    # Save segments to files
    print(f"\nAudio will be split into {len(segments)} parts.")
    for i, segment in enumerate(segments):
        output_file_path = os.path.join(output_dir, f"part_{i + 1}.mp3")
        print(f"Saving part {i + 1} ({len(segment)/1000:.2f}s) to {output_file_path}")
        segment.export(output_file_path, format="mp3")

    print(f"\nSuccessfully split audio into {len(segments)} parts using {num_desired_cuts} silences of {min_target_silence_duration}-{max_target_silence_duration}s.")

elif len(suitable_silences) > 0:
    print(f"\nFound {len(suitable_silences)} silences between {min_target_silence_duration}-{max_target_silence_duration}s, but needed {num_desired_cuts}.")
    print("Please adjust parameters or check audio if more cuts are needed at this specific duration.")
else:
    print(f"\nNo silences found between {min_target_silence_duration}s and {max_target_silence_duration}s with current parameters.")
    print(f"  (min_silence_len: {min_silence_len_param}ms, silence_thresh: {silence_thresh_param}dB)")
    print("Try adjusting 'min_silence_len_param' (e.g., to 2500ms for 2.5s) or 'silence_thresh_param' (e.g., to -35dB if silences are not very quiet, or -45dB if there's noise).")
