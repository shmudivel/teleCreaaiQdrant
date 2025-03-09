from openai import OpenAI
import os
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        prompt = """
        Анализ части текста:
        
        1. Развернуто прописать тон и характер текста
        2. Выписать все факты и цифры из текста
        3. Если есть опыт или истории Сергея Черненко, то выписать их
        4. Написать глубокий анализ текста -- помеченный форматом 1, 1.1, 1.1.1
        5. Выделить основную суть текста - ключевые идеи, которые делают его ценным для читателя
        6. Определить, какие элементы сделают контент привлекательным для аудитории Дзен:
           - Потенциальные триггеры для заголовков
           - Точки эмоционального вовлечения
           - Темы, которые могут вызвать дискуссию
        7. Идентифицировать уникальные экспертные знания автора, которые можно подчеркнуть
        
        Сохранить все пометки "--- Part X ---" из входного текста.
        """
        
        # Use the environment variable to select the model
        model = os.getenv("OPENAI_MODEL", "gpt-4o-2024-11-20")
        
        # Ensure the text is not too long for the API
        max_length = 30000  # Safe limit for most models
        truncated_text = text[:max_length] if len(text) > max_length else text
        
        response = client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": f"{prompt}\n\n{truncated_text}"
            }]
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"Error in analyze_text_structure: {str(e)}")
        # Return original text if analysis fails
        return f"Error analyzing text: {str(e)}\n\n{text}" 