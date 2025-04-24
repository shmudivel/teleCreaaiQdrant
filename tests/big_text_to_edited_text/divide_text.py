import os
import sys
import re
import requests
import json
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()

# For Claude API
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def divide_text_with_claude(text, prompt):
    """
    Uses Claude API to divide text into sections based on a prompt.
    
    Args:
        text: The text content to analyze
        prompt: The prompt to use for division
        
    Returns:
        Divided text with sections marked by "--------"
    """
    if not CLAUDE_API_KEY:
        print("Warning: ANTHROPIC_API_KEY not found in environment. Using fallback method.")
        return divide_text_fallback(text)
    
    try:
        # Create Claude client
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        
        # Enhanced prompt for more fine-grained section detection
        enhanced_prompt = prompt + """

IMPORTANT: 
1. Return the FULL ORIGINAL TEXT with divider lines inserted at the topic transitions.
2. Be generous with section divisions - create smaller, focused sections when you detect even minor topic shifts.
3. Each paragraph that introduces a new concept, example, or point should generally start a new section.
4. A typical section should be 2-4 paragraphs in length.
5. Do not summarize or remove any of the original content. Just add the divider lines where appropriate.
6. Do not add any introductory text or explanation. Start directly with the original text."""
        
        print("Sending request to Claude API using Anthropic client...")
        message = client.messages.create(
            model="claude-3-7-sonnet-20240307",
            max_tokens=8000,
            temperature=0.1,
            system="You are an AI assistant that analyzes text and divides it into logical topical sections while preserving all original content. You tend to create more fine-grained divisions rather than fewer large sections.",
            messages=[
                {"role": "user", "content": f"{enhanced_prompt}\n\nText:\n{text}"}
            ]
        )
        
        # Extract content as string from the response
        result = ""
        if hasattr(message.content, '__iter__') and not isinstance(message.content, str):
            # If content is a list or other iterable but not a string
            for item in message.content:
                if hasattr(item, 'text') and item.text:
                    result += item.text
        else:
            # If content is already a string or has a direct string representation
            result = str(message.content)
        
        # Remove any introductory text before the actual content
        intro_patterns = [
            "Here is the text divided into distinct topical sections with divider lines inserted:",
            "Here's the text with divider lines inserted at topic transitions:",
            "Here is the original text with divider lines inserted at topic transitions:",
            "Here is the text with divider lines inserted at natural topic transitions:"
        ]
        
        for pattern in intro_patterns:
            if result.strip().startswith(pattern):
                result = result.replace(pattern, "", 1).strip()
        
        # Remove any empty lines at the beginning
        result = result.lstrip("\n")
        
        return result.strip()
        
    except ImportError:
        print("Anthropic library not installed. Trying fallback API method...")
        return divide_text_with_claude_api(text, prompt)
    except Exception as e:
        print(f"Error using Claude client: {e}")
        print("Trying direct API request as fallback...")
        return divide_text_with_claude_api(text, prompt)

def divide_text_with_claude_api(text, prompt):
    """
    Uses Claude API via direct HTTP request as a fallback method.
    
    Args:
        text: The text content to analyze
        prompt: The prompt to use for division
        
    Returns:
        Divided text with sections marked by "--------"
    """
    try:
        # Enhanced prompt for more fine-grained section detection
        enhanced_prompt = prompt + """

IMPORTANT: 
1. Return the FULL ORIGINAL TEXT with divider lines inserted at the topic transitions.
2. Be generous with section divisions - create smaller, focused sections when you detect even minor topic shifts.
3. Each paragraph that introduces a new concept, example, or point should generally start a new section.
4. A typical section should be 2-4 paragraphs in length.
5. Do not summarize or remove any of the original content. Just add the divider lines where appropriate.
6. Do not add any introductory text or explanation. Start directly with the original text."""
        
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": "claude-3-7-sonnet-20240307",
            "max_tokens": 8000,
            "temperature": 0.1,
            "messages": [
                {"role": "user", "content": f"{enhanced_prompt}\n\nText:\n{text}"}
            ]
        }
        
        print("Sending request to Claude API via direct HTTP request...")
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        content = result["content"][0]["text"]
        
        # Remove any introductory text
        intro_patterns = [
            "Here is the text divided into distinct topical sections with divider lines inserted:",
            "Here's the text with divider lines inserted at topic transitions:",
            "Here is the original text with divider lines inserted at topic transitions:",
            "Here is the text with divider lines inserted at natural topic transitions:"
        ]
        
        for pattern in intro_patterns:
            if content.strip().startswith(pattern):
                content = content.replace(pattern, "", 1).strip()
        
        # Remove any empty lines at the beginning
        content = content.lstrip("\n")
        
        return content.strip()
        
    except Exception as e:
        print(f"Error using Claude API: {e}")
        print("Using fallback method for text division...")
        return divide_text_fallback(text)

def divide_text_fallback(text):
    """
    Fallback method to divide text into sections based on patterns,
    specialized for Russian text with more fine-grained section detection.
    
    Args:
        text: The text content to analyze
        
    Returns:
        Divided text with sections marked by "--------"
    """
    # Split into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    
    # If we have very few paragraphs, return as is
    if len(paragraphs) <= 3:
        return text
    
    # Find potential section breaks
    potential_breaks = []
    
    # Look for lesson headings (Урок X) - these are definite section breaks
    lesson_pattern = re.compile(r'^Урок\s+\d+\.?\s+', re.IGNORECASE)
    
    # Enhanced Russian topic transition indicators
    section_keywords = [
        'введение', 'заключение', 'вывод', 'резюме', 'часть', 'раздел', 
        'глава', 'тема', 'итог', 'пример', 'кейс', 'подход', 'метод', 
        'время', 'итак', 'итог', 'суть', 'вопрос', 'давайте', 'начнём',
        'надеюсь', 'всем привет', 'до встречи', 'первый', 'второй', 'третий',
        'четвёртый', 'следующий', 'далее', 'теперь', 'вот', 'например', 
        'представьте', 'стоит отметить', 'важно', 'интересно', 'на самом деле',
        'таким образом', 'подводя итог', 'в общем', 'ну и', 'но'
    ]
    
    # Transition phrases (these often indicate a new topic or subtopic)
    transition_phrases = [
        'но вернемся', 'давайте поговорим', 'рассмотрим', 'обратите внимание',
        'важно понимать', 'стоит отметить', 'я советую', 'запомните', 'главное',
        'ключевое', 'вернемся к', 'на мой взгляд', 'я считаю', 'как я уже говорил',
        'если вы', 'когда вы', 'во-первых', 'во-вторых', 'в-третьих', 'поэтому',
        'таким образом', 'следовательно', 'итак', 'значит', 'из этого следует',
        'это приводит', 'и наконец', 'еще один', 'кстати', 'вначале', 'также',
        'кроме того', 'с другой стороны'
    ]
    
    # Create a set of potential paragraph-starting words for new topics
    paragraph_starters = set(['я', 'мы', 'вы', 'они', 'давайте', 'нужно', 'важно', 'есть', 'был', 'была', 'были', 'имеет', 'каждый', 'любой'])
    
    # Previous paragraph first words (to detect shifts in narrative style)
    prev_first_word = None
    
    for i, para in enumerate(paragraphs[1:], 1):
        para_lower = para.lower().strip()
        
        # Empty paragraphs can't be section breaks
        if not para_lower:
            continue
        
        # Detect lesson headings (very strong indicators of section breaks)
        if lesson_pattern.search(para):
            print(f"Found lesson heading at paragraph {i}: {para[:50]}...")
            potential_breaks.append(i)
            continue
        
        # Look for numbered points, which often indicate a new section
        if re.match(r'^(\d+[\.\)、]|\([0-9a-zа-я]+\)|\•|\-)\s+', para_lower):
            potential_breaks.append(i)
            continue
            
        # Check for section-indicating keywords
        if any(keyword in para_lower for keyword in section_keywords):
            print(f"Found keyword in paragraph {i}: {para[:50]}...")
            potential_breaks.append(i)
            continue
            
        # Check first sentence for transition phrases
        first_sentence = para_lower.split('.')[0] if '.' in para_lower else para_lower
        if any(phrase in first_sentence for phrase in transition_phrases):
            potential_breaks.append(i)
            continue
            
        # Look for short paragraphs that might be section headings or transitions
        if len(para) < 200:
            if len(para.split()) < 20:  # Short paragraph
                potential_breaks.append(i)
                continue
                
        # Check for paragraphs that start with a different word pattern than previous
        words = para.split()
        if words:
            first_word = words[0].lower()
            # If we have a previous first word and it's different, might indicate a topic shift
            if prev_first_word and first_word in paragraph_starters and first_word != prev_first_word:
                potential_breaks.append(i)
            prev_first_word = first_word
            
        # Check for transitions in dialogue or changes in writing style
        if i > 1 and ":" in para and ":" not in paragraphs[i-1]:
            potential_breaks.append(i)
            continue
            
        # Check for paragraphs that start with quotes (often examples or testimonials)
        if para.strip().startswith('«') or para.strip().startswith('"'):
            potential_breaks.append(i)
            continue
            
        # Detect topic shifts based on content length differences
        # Long paragraph after several short ones or vice versa
        if i > 2:
            prev_para_len = len(paragraphs[i-1])
            current_para_len = len(para)
            if (prev_para_len < 150 and current_para_len > 400) or (prev_para_len > 400 and current_para_len < 150):
                potential_breaks.append(i)
                continue
        
        # Every 3-4 paragraphs is likely a new subtopic
        # This helps ensure we don't have extremely long sections
        if i % 4 == 0:
            potential_breaks.append(i)
    
    # Build the output with dividers
    divided_text = paragraphs[0]
    
    # Add dividers for each potential break, avoid duplicates
    unique_breaks = sorted(set(potential_breaks))
    for i, para in enumerate(paragraphs[1:], 1):
        if i in unique_breaks:
            divided_text += f"\n\n--------\n\n{para}"
        else:
            divided_text += f"\n\n{para}"
    
    return divided_text

if __name__ == "__main__":
    input_file = "document.txt"
    output_file = "divided_document.txt"
    
    # The specific prompt requested by the user with emphasis on fine-grained divisions
    prompt = """Analyze the following text and divide it into distinct topical sections by identifying meaningful semantic shifts. I've added divider lines (--------) at each natural transition point where the topic changes.

Please create smaller, more focused sections rather than large blocks. Even minor shifts in focus, examples, or concepts should start a new section."""
    
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found.")
        sys.exit(1)
    
    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        print(f"Read {len(text)} characters from {input_file}")
        
        # Divide text into sections
        print("Dividing text into sections...")
        divided_text = divide_text_with_claude(text, prompt)
        
        # Write output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(divided_text)
        
        print(f"Divided text saved to {output_file}")
        
        # Count sections
        section_count = divided_text.count("--------") + 1
        print(f"Number of sections: {section_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 