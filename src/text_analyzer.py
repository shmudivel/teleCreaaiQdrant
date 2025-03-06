from openai import OpenAI
import os

def analyze_text_structure(text):
    """
    Analyze text structure using OpenAI API.
    
    This function sends the text to OpenAI's API to generate a structured
    outline of the content with sections, subsections, and key points.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        str: A structured outline of the text content
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = """нужно супер пупер дитальную структуру текста.
    с каждого абзаца нужно выписать главный тезисы и ключевые слова. формат 1, 1.1, 1.1.1

    текст: {text}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        messages=[{
            "role": "user",
            "content": f"{prompt}\n\n{text[:20000]}"  # Truncate to fit context
        }]
    )
    
    return response.choices[0].message.content 