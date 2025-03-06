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
    Оригинальный текст:
    {text}
    Проанализируйте текст и максимально полно сохраните его структуру и содержание:
    
    1. Выделите основные смысловые блоки (Часть 1, Часть 2...)
    2. Для каждого бока:
       - Составьте иерархию подразделов (1.1, 1.2...)
       - Выделите ключевые пункты (1.1.1, 1.1.2...)
       - Сохраните оригинальные термины и формулировки
    3. Для каждого смыслового отрезка:
       - Основная мысль (дословно, где возможно)
       - Ключевые понятия (5-7 штук)
       - Важные примеры/кейсы 
       - Аргументы и выводы
    
    Формат вывода:
    ### [Название блока]
    #### [Подраздел]
    - Тезис: ...
    - Ключи: [...]
    - Примеры: [...]
    - Выводы: [...]
    
    

    """
    
    response = client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        messages=[{
            "role": "user",
            "content": f"{prompt}\n\n{text[:20000]}"  # Truncate to fit context
        }]
    )
    
    return response.choices[0].message.content 