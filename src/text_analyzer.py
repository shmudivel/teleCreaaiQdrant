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
    
    prompt = """Проанализируйте этот текст для извлечения максимально релевантной информации для индексации в векторной базе данных. Определите и структурируйте:
1. Ключевые сущности (люди, места, организации, концепции)
2. Важные взаимосвязи между сущностями
3. Специфическую терминологию предметной области и определения
4. Иерархическую структуру концепций (основные темы -> подтемы -> конкретные детали)
5. Контекстуальные ключевые слова и фразы с их значимостью

Требования к формату:
- Используйте вложенную нумерацию (1., 1.1, 1.1.1) для иерархических отношений
- Включайте как явные, так и неявные связи между концепциями
- Перечислите технические термины с их контекстуальными значениями
- Отдавайте приоритет фактическому содержанию, а не стилистическим элементам
- Включайте предложения по метаданным для эффективного поиска

Избегайте обобщений - сосредоточьтесь на структурной декомпозиции и отображении взаимосвязей."""
    
    response = client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        messages=[{
            "role": "user",
            "content": f"{prompt}\n\n{text[:15000]}"  # Truncate to fit context
        }]
    )
    
    return response.choices[0].message.content 