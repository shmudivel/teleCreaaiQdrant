import os
import json
import shutil
import anthropic
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict, Any

# Load environment variables
load_dotenv("tests/big_text_to_reels/env.")

# Initialize Anthropic client
def get_client(api_key=None):
    """Get Anthropic client with provided API key or from environment variable."""
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    return anthropic.Anthropic(api_key=api_key)

def load_metadata_files(metadata_dir: str) -> List[Dict[str, Any]]:
    """Load all metadata files from the specified directory."""
    metadata_files = []
    for filename in os.listdir(metadata_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(metadata_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Add the filename to the data for reference
                    data['filename'] = filename
                    metadata_files.append(data)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    return metadata_files

def analyze_viral_potential(metadata_files: List[Dict[str, Any]], api_key=None) -> List[Dict[str, Any]]:
    """Use Claude API to analyze and score each reel for viral potential."""
    results = []
    client = get_client(api_key)
    
    for reel_data in metadata_files:
        # Create a prompt to analyze viral potential
        prompt = f"""
You are a viral content strategist specializing in quantitative assessment. 

Analyze this reel content and rate its viral potential (1-10):

{reel_data.get('title', 'No title')}
{reel_data.get('description', 'No description')}
{reel_data.get('heygen_script', 'No script')}
Tags: {', '.join(reel_data.get('hashtags', []))}

Frame your analysis around:
- Emotional resonance and relatability
- Uniqueness and timeliness
- Value delivery (educational/entertainment)
- Audience activation potential
- Alignment with current platform trends

Return a JSON object:
{{
  "score": [1-10 integer],
  "explanation": [concise justification],
  "improvement_insight": [one key suggestion]
}}
"""
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1000,
                temperature=0,
                system="You analyze social media content and predict its viral potential. Respond only with JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract JSON from response
            response_text = message.content[0].text
            # Try to parse the response as JSON
            try:
                analysis = json.loads(response_text)
                # Add the analysis to the reel data
                reel_data['viral_analysis'] = analysis
                results.append(reel_data)
                print(f"Analyzed {reel_data['filename']} - Score: {analysis.get('score', 'N/A')}")
            except json.JSONDecodeError:
                # If we can't parse as JSON, extract score using simple parsing
                if 'score' in response_text.lower():
                    try:
                        score_text = response_text.lower().split('score')[1]
                        # Extract digits
                        score = ''.join(filter(str.isdigit, score_text[:10]))
                        if score:
                            reel_data['viral_analysis'] = {
                                'score': int(score),
                                'explanation': response_text
                            }
                            results.append(reel_data)
                            print(f"Analyzed {reel_data['filename']} - Score: {score}")
                    except Exception as e:
                        print(f"Error extracting score from response: {e}")
                        reel_data['viral_analysis'] = {'score': 0, 'explanation': 'Failed to parse response'}
                        results.append(reel_data)
        except Exception as e:
            print(f"Error analyzing {reel_data.get('filename', 'unknown file')}: {e}")
            reel_data['viral_analysis'] = {'score': 0, 'explanation': f'API error: {str(e)}'}
            results.append(reel_data)
    
    return results

def select_top_reels(analyzed_reels: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    """Select the top n reels based on viral potential score."""
    # Sort by score from highest to lowest
    sorted_reels = sorted(
        analyzed_reels, 
        key=lambda x: x.get('viral_analysis', {}).get('score', 0), 
        reverse=True
    )
    
    # Return top n reels
    return sorted_reels[:top_n]

def save_top_reels(top_reels: List[Dict[str, Any]], metadata_dir: str, output_dir: str):
    """Save the top reels to a new directory."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for reel in top_reels:
        filename = reel.get('filename')
        if filename:
            source_path = os.path.join(metadata_dir, filename)
            dest_path = os.path.join(output_dir, filename)
            
            try:
                # Copy the original file
                shutil.copy2(source_path, dest_path)
                
                # Also save the analysis
                analysis_filename = f"analysis_{filename}"
                analysis_path = os.path.join(output_dir, analysis_filename)
                with open(analysis_path, 'w', encoding='utf-8') as f:
                    json.dump(reel, f, ensure_ascii=False, indent=2)
                
                print(f"Saved {filename} to {output_dir}")
            except Exception as e:
                print(f"Error saving {filename}: {e}")

def main():
    # Define paths
    metadata_dir = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/tests/big_text_to_reels/output/metadata"
    output_dir = "/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/tests/big_text_to_reels/output/top_reels"
    
    # Create output directory path
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"Loading metadata files from {metadata_dir}...")
    metadata_files = load_metadata_files(metadata_dir)
    print(f"Loaded {len(metadata_files)} metadata files.")
    
    print("Analyzing viral potential with Claude API...")
    analyzed_reels = analyze_viral_potential(metadata_files)
    
    print("Selecting top 10 viral reels...")
    top_reels = select_top_reels(analyzed_reels, top_n=10)
    
    print(f"Saving top reels to {output_dir}...")
    save_top_reels(top_reels, metadata_dir, output_dir)
    
    print("Done! Top 10 viral reels have been saved.")
    
    # Print summary of top reels
    print("\nTop 10 Viral Reels Summary:")
    for i, reel in enumerate(top_reels, 1):
        score = reel.get('viral_analysis', {}).get('score', 'N/A')
        title = reel.get('title', 'No title')
        filename = reel.get('filename', 'Unknown file')
        print(f"{i}. {filename} - {title} (Score: {score})")

if __name__ == "__main__":
    main() 