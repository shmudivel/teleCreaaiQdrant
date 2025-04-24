import os
import re
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# For Claude API
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

def split_text_to_markdown(text, output_dir):
    """
    Splits the divided text into separate markdown files.
    
    Args:
        text: The text content with sections divided by "--------" markers.
        output_dir: Directory to save the markdown files.
        
    Returns:
        A list of paths to the created markdown files.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # First check if we need to use Claude to split the text
    if "--------" not in text:
        try:
            # Using Claude 3.7 for text splitting
            headers = {
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            payload = {
                "model": "claude-3-7-sonnet-20240307",
                "max_tokens": 4096,
                "temperature": 0.3,
                "messages": [
                    {"role": "user", "content": f'Split the provided text into separate markdown files. '
                     f'Each natural section or topic should become its own section. '
                     f'Mark the end of each section with "--------". '
                     f'Use the first line of each section as a title.\n\n{text}'}
                ]
            }
            
            response = requests.post(CLAUDE_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            text = result["content"][0]["text"]
        except Exception as e:
            print(f"Error using Claude API for splitting: {e}")
            # Continue with the original text if Claude fails
    
    # Split the text by the divider
    sections = text.split("--------")
    
    # Process each section and create a markdown file
    file_paths = []
    
    for i, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue
            
        # Extract the first line as the title
        lines = section.split('\n')
        title = lines[0].strip()
        
        # Clean the title to make it suitable for a filename
        clean_title = re.sub(r'[^\w\s-]', '', title).strip().lower()
        clean_title = re.sub(r'[-\s]+', '-', clean_title)
        
        # If title is empty or too short, use a default name
        if len(clean_title) < 3:
            clean_title = f"section-{i+1}"
            
        # Ensure filename uniqueness
        file_name = f"{clean_title}.md"
        file_path = os.path.join(output_dir, file_name)
        
        # If file exists, add a number to make it unique
        counter = 1
        while os.path.exists(file_path):
            file_name = f"{clean_title}-{counter}.md"
            file_path = os.path.join(output_dir, file_name)
            counter += 1
        
        # Write the section to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            # Add the rest of the section content, skipping the title
            f.write("\n".join(lines[1:]))
        
        file_paths.append(file_path)
        print(f"Created file: {file_path}")
    
    return file_paths

if __name__ == "__main__":
    # Test with sample divided text if this file is run directly
    sample_divided_text = """Introduction to Artificial Intelligence

Artificial Intelligence (AI) is a field of computer science that focuses on creating systems capable of performing tasks that typically require human intelligence. These tasks include learning, reasoning, problem-solving, perception, and language understanding.

--------

The History of AI

The concept of artificial intelligence dates back to ancient times, with myths, stories, and rumors of artificial beings endowed with intelligence or consciousness by master craftsmen. However, the field of AI research was founded at a workshop held on the campus of Dartmouth College during the summer of 1956.

--------

Machine Learning and Deep Learning

Machine learning is a subset of AI that provides systems the ability to automatically learn and improve from experience without being explicitly programmed. Deep learning is a subset of machine learning that uses neural networks with many layers to analyze various factors of data.
"""
    
    test_output_dir = "test_output"
    file_paths = split_text_to_markdown(sample_divided_text, test_output_dir)
    print(f"Created {len(file_paths)} markdown files in {test_output_dir}") 