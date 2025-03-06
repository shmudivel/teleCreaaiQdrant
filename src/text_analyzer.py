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
    
    prompt = """Составь максимально подробную структуру текста . Разбей на разделы и подпункты, используя заголовки, и перечисли ключевые слова и фразы, которые помогут быстро вспомнить содержание. Структура должна быть логичной и удобной для использования. Укажи основные тезисы, аргументы и примеры, и как можно больше существительных. для каждой новой линии формат глав и подглав 1. , 1.1, 1.1.1:
    """
    
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{
            "role": "user",
            "content": f"{prompt}\n\n{text[:15000]}"  # Truncate to fit context
        }]
    )
    
    return response.choices[0].message.content 