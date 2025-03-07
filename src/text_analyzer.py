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
    
    prompt = """
    написать глубокий анализ текста -- помеченный форматом 1, 1.1, 1.1.1
    главная мысль текста: не уходите в свой бизнес, продолжайте работать в найме

    НЕ ТРОГАТЬ И НЕ ДОБАВЛЯТЬ части "--- Part 1 ---", "--- Part 2 ---", "--- Part 3 ---", "--- Part 4 ---"
    после каждой части (их 4 всего) --- Part ... --- развернуто прописать тон и характер текста
    выписывать все факты и цифры из текста

    если есть что-то про авторитетность Сергея Черненко, то прописывайте его авторитетность
    
    
    
    
    

    

    """
    
    response = client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        messages=[{
            "role": "user",
            "content": f"{prompt}\n\n{text[:30000]}"  # Truncate to fit context
        }]
    )
    
    return response.choices[0].message.content 