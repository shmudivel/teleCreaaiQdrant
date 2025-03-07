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

    главная мысль текста: не уходите в свой бизнес, продолжайте работать в найме

    НЕ ТРОГАТЬ пометку "--- Part 1 ---", 
    развернуто прописать тон и характер текста
    выписать все факты и цифры из текста
    если есть опыт или истории Сергея Черненко, то выписать их
    написать глубокий анализ текста -- помеченный форматом 1, 1.1, 1.1.1
    
    НЕ ТРОГАТЬ пометку "--- Part 2 ---", 
    развернуто прописать тон и характер текста
    выписать все факты и цифры из текста
    если есть опыт или истории Сергея Черненко, то выписать их
    написать глубокий анализ текста -- помеченный форматом 1, 1.1, 1.1.1

    НЕ ТРОГАТЬ пометку "--- Part 3 ---", 
    развернуто прописать тон и характер текста
    выписать все факты и цифры из текста
    если есть опыт или истории Сергея Черненко, то выписать их
    написать глубокий анализ текста -- помеченный форматом 1, 1.1, 1.1.1

    НЕ ТРОГАТЬ пометку "--- Part 4 ---"
    развернуто прописать тон и характер текста
    выписать все факты и цифры из текста
    если есть опыт или истории Сергея Черненко, то выписать их
    написать глубокий анализ текста -- помеченный форматом 1, 1.1, 1.1.1
    
    

    

    """
    
    response = client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        messages=[{
            "role": "user",
            "content": f"{prompt}\n\n{text[:30000]}"  # Truncate to fit context
        }]
    )
    
    return response.choices[0].message.content 