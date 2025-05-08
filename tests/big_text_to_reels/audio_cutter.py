import os
from pydub import AudioSegment
from pydub.silence import detect_silence

# Path to the audio file
input_file = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/tests/big_text_to_reels/ElevenLabs_2025-05-07T12_30_41_Тест_pvc_sp100_s50_sb75_se0_b_m2.mp3"
output_dir = os.path.dirname(input_file)

# Load the audio file
print(f"Loading audio file: {input_file}")
audio = AudioSegment.from_mp3(input_file)

# Detect silent parts (min_silence_len in ms, silence_thresh in dB)
print("Detecting silent parts...")
silent_parts = detect_silence(
    audio, 
    min_silence_len=1000,  # 1 second minimum for silence detection
    silence_thresh=-40     # -40 dB threshold for silence
)

# Convert silent parts to seconds for easier handling
silent_parts_sec = [(start/1000, end/1000) for start, end in silent_parts]
print(f"Found {len(silent_parts_sec)} silent parts")

# Find silent parts that are 3-5 seconds long
suitable_silences = [
    (start, end) for start, end in silent_parts_sec 
    if 3 <= (end - start) <= 5
]
print(f"Found {len(suitable_silences)} suitable silence parts (3-5 seconds)")

# If we don't have enough suitable silences, fall back to any silence over 1 second
if len(suitable_silences) < 3:
    print("Not enough suitable silence parts, falling back to any silence > 1 second")
    suitable_silences = [
        (start, end) for start, end in silent_parts_sec 
        if (end - start) >= 1
    ]

# Sort silences by position and try to pick 3 that divide the audio evenly
if len(suitable_silences) >= 3:
    total_duration = len(audio) / 1000  # total duration in seconds
    target_points = [total_duration / 4, total_duration / 2, 3 * total_duration / 4]
    
    # Find silences closest to our target division points
    cut_points = []
    for target in target_points:
        closest = min(suitable_silences, key=lambda x: abs(x[0] - target))
        cut_points.append(closest)
        # Remove this silence to avoid picking the same one twice
        suitable_silences.remove(closest)
    
    # Sort cut points by time
    cut_points.sort(key=lambda x: x[0])
    
    # Convert back to milliseconds for pydub
    cut_points_ms = [(int(start * 1000), int(end * 1000)) for start, end in cut_points]
    
    # Buffer for ensuring words are fully spoken (in milliseconds)
    buffer_ms = 1000  # 0.4 seconds
    
    # Create the segments
    segments = []
    last_cut = 0
    
    for i, (start, end) in enumerate(cut_points_ms):
        # Add segment from last cut to start of silence plus a small buffer
        cut_point = start + buffer_ms  # Add buffer after the word ends
        segments.append(audio[last_cut:cut_point])
        last_cut = end  # Resume from end of silence
    
    # Add the final segment
    segments.append(audio[last_cut:])
    
    # Save segments to files
    for i, segment in enumerate(segments):
        output_file = os.path.join(output_dir, f"part_{i+1}.mp3")
        print(f"Saving part {i+1} to {output_file}")
        segment.export(output_file, format="mp3")
    
    print(f"Successfully split audio into {len(segments)} parts")
else:
    print("Not enough silence parts found to split the audio into 4 segments.") 