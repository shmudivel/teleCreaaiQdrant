import os
from openai import OpenAI
from pathlib import Path

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def generate_srt_from_audio(audio_file_path: str, words_per_subtitle: int = 1):
    """
    Generates an SRT subtitle file from an audio file using OpenAI's Whisper model.
    Creates subtitles with 1-2 words per entry for better readability.

    Args:
        audio_file_path (str): The path to the audio file.
        words_per_subtitle (int): Number of words per subtitle entry (default: 1)
    """
    if not os.path.exists(audio_file_path):
        print(f"Error: Audio file not found at {audio_file_path}")
        return

    try:
        # Ensure the OPENAI_API_KEY environment variable is set.
        client = OpenAI()
        # Set your OpenAI API key in the OPENAI_API_KEY environment variable

        print(f"Transcribing audio file: {audio_file_path}")

        # Get word-level transcription with timestamps
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )

        # Group words into chunks of 1-2 words
        words = transcript.words
        srt_entries = []
        
        i = 0
        while i < len(words):
            # Take 1-2 words for this subtitle entry
            end_index = min(i + words_per_subtitle, len(words))
            word_chunk = words[i:end_index]
            
            if word_chunk:
                start_time = word_chunk[0].start
                end_time = word_chunk[-1].end
                text = ' '.join([word.word for word in word_chunk])
                
                # Format as SRT entry
                srt_entry = f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}\n"
                srt_entry += f"{text.strip()}\n\n"
                
                srt_entries.append(srt_entry)
            
            i = end_index

        # Write to SRT file
        srt_file_path = Path(audio_file_path).with_suffix(".srt")
        
        with open(srt_file_path, "w", encoding="utf-8") as srt_file:
            srt_file.writelines(srt_entries)

        print(f"SRT file successfully generated at: {srt_file_path}")
        print(f"Generated {len(srt_entries)} subtitle entries with {words_per_subtitle} words each")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Path to the audio file you provided.
    audio_path = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/tests/subtitles/testSubtitlesGenWithShotstack/ElevenLabs_2025-06-11T09_14_11_Тест_pvc_sp109_s50_sb75_t2-5.mp3"
    generate_srt_from_audio(audio_path, words_per_subtitle=1) 