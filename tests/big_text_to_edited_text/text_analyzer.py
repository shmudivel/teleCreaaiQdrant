import re
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# For Claude API
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

def analyze_and_divide_text(text):
    """
    Analyzes the given text and divides it into distinct topical sections.
    
    Args:
        text: The text content to analyze.
        
    Returns:
        A string with sections divided by "--------" markers.
    """
    # Check if text is empty or too short to meaningfully divide
    if not text or len(text) < 500:
        return text
    
    try:
        # Using Claude 3.7 for text analysis
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
                {"role": "user", "content": f"Analyze the following text and divide it into distinct topical sections. "
                 f"For each natural transition between topics, insert a divider line (--------) "
                 f"to clearly mark where one topic ends and another begins. "
                 f"Focus on identifying meaningful semantic shifts rather than arbitrary divisions.\n\n{text}"}
            ]
        }
        
        response = requests.post(CLAUDE_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        divided_text = result["content"][0]["text"]
        return divided_text
    
    except Exception as e:
        print(f"Error using Claude API: {e}")
        print("Using fallback method for text division...")
        
        # Fallback: Basic paragraph-based division
        # This is a simplistic approach that might not catch semantic transitions as well
        paragraphs = re.split(r'\n\s*\n', text)
        
        # If we have very few paragraphs, return as is
        if len(paragraphs) <= 3:
            return text
            
        # Find potential section breaks based on paragraph length and keywords
        potential_breaks = []
        
        # Look for paragraphs that might indicate a topic change
        section_keywords = ['introduction', 'conclusion', 'summary', 'background', 
                           'method', 'results', 'discussion', 'chapter', 'section', 
                           'part', 'overview']
        
        for i, para in enumerate(paragraphs[1:-1], 1):  # Skip first and last paragraph
            # Short paragraphs might indicate transitions
            if len(para) < 100:
                # Check for section indicator words
                if any(keyword in para.lower() for keyword in section_keywords):
                    potential_breaks.append(i)
                    
            # Long paragraphs after short ones might indicate new sections
            elif i > 0 and len(paragraphs[i-1]) < 100 and len(para) > 300:
                potential_breaks.append(i)
        
        # Build the output with dividers
        divided_text = paragraphs[0]
        
        for i, para in enumerate(paragraphs[1:], 1):
            if i in potential_breaks:
                divided_text += f"\n\n--------\n\n{para}"
            else:
                divided_text += f"\n\n{para}"
        
        return divided_text

if __name__ == "__main__":
    # Test with sample text if this file is run directly
    sample_text = """
    Introduction to Artificial Intelligence
    
    Artificial Intelligence (AI) is a field of computer science that focuses on creating systems capable of performing tasks that typically require human intelligence. These tasks include learning, reasoning, problem-solving, perception, and language understanding.
    
    The History of AI
    
    The concept of artificial intelligence dates back to ancient times, with myths, stories, and rumors of artificial beings endowed with intelligence or consciousness by master craftsmen. However, the field of AI research was founded at a workshop held on the campus of Dartmouth College during the summer of 1956.
    
    Machine Learning
    
    Machine learning is a subset of AI that provides systems the ability to automatically learn and improve from experience without being explicitly programmed. Machine learning focuses on the development of computer programs that can access data and use it to learn for themselves.
    
    Deep Learning
    
    Deep learning is a subset of machine learning that uses neural networks with many layers (hence "deep") to analyze various factors of data. It is inspired by the structure and function of the brain, specifically the interconnecting of many neurons.
    """
    
    divided = analyze_and_divide_text(sample_text)
    print(divided) 