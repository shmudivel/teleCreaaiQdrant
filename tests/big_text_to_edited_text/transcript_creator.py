import os
import re
import math
import random
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# For Claude API
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

def create_timestamped_transcript(md_files, output_dir):
    """
    Creates a timestamped transcription of the content in the provided markdown files.
    
    Args:
        md_files: List of paths to markdown files to process.
        output_dir: Directory to save the transcript files.
        
    Returns:
        A list of paths to the created transcript files.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    transcript_files = []
    
    for md_file in md_files:
        # Read markdown file content
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract the filename without extension
        base_name = os.path.basename(md_file)
        file_name_without_ext = os.path.splitext(base_name)[0]
        
        # Create transcript file path
        transcript_file = os.path.join(output_dir, f"{file_name_without_ext}_transcript.md")
        
        try:
            # Using Claude 3.7 for transcript generation
            headers = {
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            prompt = f'''Create a timestamped transcription of the content in the provided text. 
Format your output as follows:
1. List each significant segment chronologically 
2. Include timestamps in [HH:MM:SS] format at the beginning of each entry 
3. Format the transcription similar to YouTube's auto-generated captions, with clear speaker attribution when possible 
4. Number each timestamped entry sequentially 
5. Capture key moments, topics, or speaker changes
Example format: 
1. [00:01:15] Speaker A: First significant statement or topic 
2. [00:03:42] Speaker B: Response or new topic introduction
Create a simulated timestamped transcript based on reasonable assumptions about timing.

Here's the content to transcribe:
{content}'''
            
            payload = {
                "model": "claude-3-7-sonnet-20240307",
                "max_tokens": 4096,
                "temperature": 0.5,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = requests.post(CLAUDE_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            transcript = result["content"][0]["text"]
            
        except Exception as e:
            print(f"Error using Claude API for transcript: {e}")
            print("Using fallback method for transcript generation...")
            
            # Fallback: Generate basic transcript with timestamps
            transcript = generate_fallback_transcript(content)
        
        # Write transcript to file
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcript)
            
        transcript_files.append(transcript_file)
        print(f"Created transcript: {transcript_file}")
    
    return transcript_files

def generate_fallback_transcript(content):
    """
    Fallback method to generate a basic transcript with timestamps.
    
    Args:
        content: The markdown content to process.
        
    Returns:
        A string containing the timestamped transcript.
    """
    # Extract title and text content
    match = re.match(r'#\s+(.*?)(?:\n|$)(.*)', content, re.DOTALL)
    if match:
        title = match.group(1).strip()
        text = match.group(2).strip()
    else:
        title = "Untitled Section"
        text = content.strip()
    
    # Split into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Generate transcript
    transcript_lines = [f"# Timestamped Transcript: {title}\n"]
    
    # Estimate a reasonable video length based on content length
    # Assuming average speaking rate of 150 words per minute
    word_count = sum(len(para.split()) for para in paragraphs)
    estimated_minutes = max(5, math.ceil(word_count / 150))  # Minimum 5 minutes
    
    # Create some speaker variations
    speakers = ["Host", "Speaker A", "Speaker B", "Guest"]
    
    # Track current timestamp in seconds
    current_time = random.randint(0, 60)  # Start at a random time within first minute
    
    for i, para in enumerate(paragraphs):
        if not para.strip():
            continue
            
        # Split long paragraphs into smaller segments
        words = para.split()
        segments = []
        
        if len(words) > 50:
            # Split into segments of roughly 20-40 words
            segment_size = random.randint(20, 40)
            for j in range(0, len(words), segment_size):
                segment = ' '.join(words[j:j+segment_size])
                segments.append(segment)
        else:
            segments.append(para)
        
        for segment in segments:
            # Format timestamp
            hours = current_time // 3600
            minutes = (current_time % 3600) // 60
            seconds = current_time % 60
            timestamp = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
            
            # Choose speaker
            if i == 0:
                speaker = "Host"  # First paragraph is typically the host/intro
            else:
                speaker = random.choice(speakers)
                
            # Add to transcript
            entry_num = len(transcript_lines)  # Use current line count as entry number
            transcript_lines.append(f"{entry_num}. {timestamp} {speaker}: {segment}")
            
            # Increment time based on word count (approx. 3 words per second)
            word_count = len(segment.split())
            time_increment = max(3, word_count // 3)  # At least 3 seconds per segment
            current_time += time_increment
    
    return "\n\n".join(transcript_lines)

if __name__ == "__main__":
    # Test with sample markdown file if this file is run directly
    import tempfile
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a sample markdown file
        sample_md = os.path.join(temp_dir, "sample.md")
        with open(sample_md, 'w', encoding='utf-8') as f:
            f.write("""# Introduction to AI Ethics
            
Artificial Intelligence systems are becoming increasingly prevalent in our daily lives. From recommending products to diagnosing diseases, AI is transforming how we interact with technology.

However, with this increased adoption comes important ethical considerations. How do we ensure AI systems are fair, transparent, and accountable? Who is responsible when an AI makes a mistake?

These questions form the foundation of AI ethics, an emerging field dedicated to addressing the moral implications of artificial intelligence.""")
        
        # Generate transcript
        transcript_files = create_timestamped_transcript([sample_md], temp_dir)
        
        # Print the transcript
        with open(transcript_files[0], 'r', encoding='utf-8') as f:
            print(f.read()) 