from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
import time
import json
from json.decoder import JSONDecodeError

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
        str: A structured outline of the text content or JSON object
    """
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            prompt = """
            Анализ текста по частям:
            
            Для каждой части:
            
            НЕ ТРОГАТЬ пометку "--- Part 1 ---", "--- Part 2 ---", и т.д.
            
            1. ТЩАТЕЛЬНО ПРОАНАЛИЗИРОВАТЬ ТОН И СТИЛЬ автора:
               - Определить эмоциональный тон (формальный, неформальный, агрессивный, мотивирующий и т.д.)
               - Выявить лексические особенности (экспертные термины, разговорные выражения)
               - Определить синтаксические особенности (длина предложений, сложность структуры)
               - Определить риторические приемы (метафоры, аналогии, истории)
               - Выделить авторский "голос" и манеру изложения мыслей
            
            2. ВЫДЕЛИТЬ КЛЮЧЕВЫЕ ЭЛЕМЕНТЫ:
               - Все факты и цифры из текста
               - Истории и личный опыт автора
               - Основные идеи и аргументы
               - Уникальные инсайты и экспертные знания
            
            3. ГЛУБОКИЙ АНАЛИЗ СОДЕРЖАНИЯ:
               - Определить главную идею каждой части
               - Выявить логические связи между абзацами
               - Выделить основную суть текста и его ценность для читателя
               - Найти причинно-следственные связи в аргументации
               - Определить цель автора и послание к аудитории
            
            В конце анализа добавить:
            1. ЦЕЛОСТНЫЙ АНАЛИЗ текста:
               - Обобщение основной стилистики и тона всего текста
               - Связность и логика изложения между частями
               - Главные эмоциональные триггеры и якоря внимания
               - Авторские особенности, делающие текст уникальным
            
            2. ПОТЕНЦИАЛ ДЛЯ ДЗЕН:
               - Определить элементы, которые сделают контент привлекательным для аудитории Дзен
               - Потенциальные триггеры для заголовков
               - Точки эмоционального вовлечения
               - Темы, которые могут вызвать дискуссию
               - Соответствие интересам целевой аудитории
            
            ВАЖНО: верни ответ в следующем JSON формате:
            {
              "parts": [
                {
                  "marker": "--- Part 1 ---",
                  "tone_analysis": {
                    "emotional_tone": "описание эмоционального тона",
                    "lexical_features": "особенности лексики",
                    "syntax_patterns": "синтаксические особенности",
                    "rhetorical_devices": "риторические приемы",
                    "author_voice": "авторский голос и манера"
                  },
                  "key_elements": {
                    "facts": ["факт 1", "факт 2", ...],
                    "personal_stories": ["история 1", ...],
                    "main_ideas": ["идея 1", "идея 2", ...],
                    "unique_insights": ["инсайт 1", ...]
                  },
                  "content_analysis": {
                    "main_idea": "главная идея части",
                    "paragraph_connections": "связи между абзацами",
                    "key_essence": "основная суть текста",
                    "logic_path": "логический путь аргументации",
                    "author_intention": "цель автора в этой части"
                  }
                },
                // аналогично для других частей
              ],
              "holistic_analysis": {
                "overall_style": "обобщение стиля всего текста",
                "coherence": "связность между частями",
                "emotional_triggers": ["триггер 1", "триггер 2", ...],
                "author_uniqueness": ["особенность 1", "особенность 2", ...]
              },
              "dzen_potential": {
                "attention_hooks": ["крючок 1", "крючок 2", ...],
                "emotional_points": ["точка 1", "точка 2", ...],
                "discussion_topics": ["тема 1", "тема 2", ...],
                "audience_relevance": "соответствие интересам целевой аудитории"
              }
            }
            """
            
            # Use the environment variable to select the model
            model = os.getenv("OPENAI_MODEL", "gpt-4o-2024-11-20")
            
            # Ensure the text is not too long for the API
            max_length = 30000  # Safe limit for most models
            
            # Improved handling of long texts while preserving parts structure
            if len(text) > max_length:
                # Find part markers
                part_markers = ["--- Part 1 ---", "--- Part 2 ---", "--- Part 3 ---", "--- Part 4 ---"]
                parts = {}
                
                # Extract each part
                for i in range(len(part_markers)):
                    start_marker = part_markers[i]
                    start_pos = text.find(start_marker)
                    
                    if start_pos == -1:
                        continue
                        
                    # Find end of this part (start of next part or end of text)
                    if i < len(part_markers) - 1:
                        end_marker = part_markers[i+1]
                        end_pos = text.find(end_marker)
                        if end_pos == -1:
                            part_text = text[start_pos:]
                        else:
                            part_text = text[start_pos:end_pos]
                    else:
                        part_text = text[start_pos:]
                    
                    # Truncate each part if needed
                    max_part_length = max_length // len(part_markers)
                    if len(part_text) > max_part_length:
                        parts[start_marker] = part_text[:max_part_length]
                    else:
                        parts[start_marker] = part_text
                
                # Reconstruct text with truncated parts
                truncated_text = ""
                for marker in part_markers:
                    if marker in parts:
                        truncated_text += parts[marker]
            else:
                truncated_text = text
            
            response = client.chat.completions.create(
                model=model,
                temperature=0.6,  # Slightly lower temperature for more accurate tone analysis
                response_format={"type": "json_object"},  # Request JSON response
                messages=[{
                    "role": "user",
                    "content": f"{prompt}\n\n{truncated_text}"
                }]
            )
            
            content = response.choices[0].message.content
            
            # Validate JSON structure
            try:
                json_content = json.loads(content)
                return content  # Return the valid JSON string
            except JSONDecodeError:
                logger.warning(f"Received invalid JSON on attempt {attempt+1}, retrying...")
                if attempt == max_retries - 1:  # If last attempt
                    # Fall back to returning raw text if JSON parsing consistently fails
                    return content
                time.sleep(retry_delay)
                continue
        
        except Exception as e:
            logger.error(f"Error in analyze_text_structure (attempt {attempt+1}): {str(e)}")
            if attempt < max_retries - 1:
                # Only retry if not the last attempt
                time.sleep(retry_delay)
            else:
                # Return original text if all retries fail
                return f"Error analyzing text after {max_retries} attempts: {str(e)}\n\n{text}" 

def extract_insights(analysis_json, insight_type=None):
    """
    Extract specific insights from the JSON analysis result.
    
    Args:
        analysis_json (str): JSON string from analyze_text_structure
        insight_type (str, optional): Type of insight to extract. Options:
            - 'tone_analysis' - Get tone analysis for all parts
            - 'key_elements' - Get key elements from all parts
            - 'holistic_analysis' - Get holistic analysis of the text
            - 'dzen_potential' - Get Dzen-specific potential insights
            - 'author_voice' - Get author's voice characteristics
            - None - Return the full parsed JSON
    
    Returns:
        dict or list: Extracted insights based on the requested type
    """
    try:
        # Parse JSON if string is provided
        if isinstance(analysis_json, str):
            data = json.loads(analysis_json)
        else:
            data = analysis_json
            
        if insight_type is None:
            return data
            
        if insight_type == 'tone_analysis':
            return [part.get('tone_analysis', {}) for part in data.get('parts', [])]
            
        elif insight_type == 'key_elements':
            all_elements = {}
            for part in data.get('parts', []):
                elements = part.get('key_elements', {})
                for key, values in elements.items():
                    if key not in all_elements:
                        all_elements[key] = []
                    all_elements[key].extend(values)
            return all_elements
            
        elif insight_type == 'holistic_analysis':
            return data.get('holistic_analysis', {})
            
        elif insight_type == 'dzen_potential':
            return data.get('dzen_potential', {})
            
        elif insight_type == 'author_voice':
            author_voices = []
            for part in data.get('parts', []):
                tone = part.get('tone_analysis', {})
                if 'author_voice' in tone:
                    author_voices.append(tone['author_voice'])
            return author_voices
            
        else:
            logger.warning(f"Unknown insight type: {insight_type}")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting insights: {str(e)}")
        return None 