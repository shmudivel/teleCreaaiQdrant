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
            
            НЕ ТРОГАТЬ пометку "--- Part 1 ---", 
            развернуто прописать тон и характер текста
            выписать все факты и цифры из текста
            если есть опыт или истории Сергея Черненко, то выписать их
            написать глубокий анализ текста -- помеченный форматом 1, 1.1, 1.1.1
            выделить основную суть текста - ключевые идеи, которые делают его ценным для читателя
            
            НЕ ТРОГАТЬ пометку "--- Part 2 ---", 
            развернуто прописать тон и характер текста
            выписать все факты и цифры из текста
            если есть опыт или истории Сергея Черненко, то выписать их
            написать глубокий анализ текста -- помеченный форматом 1, 1.1, 1.1.1
            выделить основную суть текста - ключевые идеи, которые делают его ценным для читателя
            
            НЕ ТРОГАТЬ пометку "--- Part 3 ---", 
            развернуто прописать тон и характер текста
            выписать все факты и цифры из текста
            если есть опыт или истории Сергея Черненко, то выписать их
            написать глубокий анализ текста -- помеченный форматом 1, 1.1, 1.1.1
            выделить основную суть текста - ключевые идеи, которые делают его ценным для читателя
            
            НЕ ТРОГАТЬ пометку "--- Part 4 ---",
            развернуто прописать тон и характер текста
            выписать все факты и цифры из текста
            если есть опыт или истории Сергея Черненко, то выписать их
            написать глубокий анализ текста -- помеченный форматом 1, 1.1, 1.1.1
            выделить основную суть текста - ключевые идеи, которые делают его ценным для читателя
            
            В конце анализа добавить для всего текста:
            1. Определить, какие элементы сделают контент привлекательным для аудитории Дзен:
               - Потенциальные триггеры для заголовков
               - Точки эмоционального вовлечения
               - Темы, которые могут вызвать дискуссию
            2. Идентифицировать уникальные экспертные знания автора, которые можно подчеркнуть
            
            ВАЖНО: верни ответ в следующем JSON формате:
            {
              "parts": [
                {
                  "marker": "--- Part 1 ---",
                  "tone": "описание тона и характера",
                  "facts": ["факт 1", "факт 2", ...],
                  "personal_stories": ["история 1", ...],
                  "analysis": {"1": "...", "1.1": "...", ...},
                  "key_essence": "основная суть этой части"
                },
                // аналогично для других частей
              ],
              "engagement": {
                "headline_triggers": ["триггер 1", "триггер 2", ...],
                "emotional_points": ["точка 1", "точка 2", ...],
                "discussion_topics": ["тема 1", "тема 2", ...]
              },
              "expertise": ["экспертные знания 1", "экспертные знания 2", ...]
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
                temperature=0.7,  # Add creativity parameter - higher values for more creative analysis
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
            - 'headline_triggers' - Get potential headline hooks
            - 'key_essence' - Get the key essence from all parts
            - 'expertise' - Get author's expertise highlights
            - 'facts' - Get all facts and figures
            - 'emotional_points' - Get emotional engagement points
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
            
        if insight_type == 'headline_triggers':
            return data.get('engagement', {}).get('headline_triggers', [])
            
        elif insight_type == 'key_essence':
            return [part.get('key_essence', '') for part in data.get('parts', [])]
            
        elif insight_type == 'expertise':
            return data.get('expertise', [])
            
        elif insight_type == 'facts':
            all_facts = []
            for part in data.get('parts', []):
                all_facts.extend(part.get('facts', []))
            return all_facts
            
        elif insight_type == 'emotional_points':
            return data.get('engagement', {}).get('emotional_points', [])
            
        else:
            logger.warning(f"Unknown insight type: {insight_type}")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting insights: {str(e)}")
        return None 