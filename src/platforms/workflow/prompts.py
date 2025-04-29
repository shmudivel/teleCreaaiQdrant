"""
Prompts used in the Content-to-Reels workflow.

This module centralizes all prompts used in the workflow to make them
easier to modify and maintain.
"""

# 1. Document Analysis Prompt
# Used in: src/platforms/workflow/analyze_google_doc.py -> analyze_with_claude() function
# Purpose: Divide a Google Doc into topical sections
DOC_ANALYSIS_PROMPT = """Analyze the following text and divide it into distinct topical sections. 
    
For each natural transition between topics, insert a divider line (--------) to clearly mark where one topic ends and another begins. Focus on identifying meaningful semantic shifts rather than arbitrary divisions.

IMPORTANT: 
1. Return the FULL ORIGINAL TEXT with divider lines inserted at the topic transitions. 
2. Do not summarize or remove any of the original content. Just add the divider lines where appropriate.
3. Do not add any introductory text or explanation. Start directly with the original text."""

# System prompt for document analysis
# Used in: src/platforms/workflow/analyze_google_doc.py -> analyze_with_claude() function
DOC_ANALYSIS_SYSTEM_PROMPT = "You are an AI assistant that analyzes text and divides it into logical topical sections while preserving all original content. Do not add any introductory text or explanation."


# 2. Reel Script Generation Prompt
# Used in: src/platforms/workflow/create_reel_scripts.py -> ReelGenerator.generate_reel_script() method
# Purpose: Transform each section into an Instagram reel script
REEL_GENERATION_PROMPT = """
You are a skilled Instagram reel script writer. Your task is to transform the following text section into an engaging, 
informative reel script that educates and resonates with the audience.

ВАЖНО: ВСЕ ОТВЕТЫ ДОЛЖНЫ БЫТЬ НА РУССКОМ ЯЗЫКЕ, включая сценарий, описание, хэштеги и все остальные поля.

SECTION INFORMATION:
Title: {title}

MAIN CONTENT TO TRANSFORM:
{content}

INSTRUCTIONS:
1. Create a reel script based on the MAIN CONTENT.
2. Make the script engaging, concise, and suitable for an Instagram reel (60-90 seconds).
3. Keep the core message and educational value of the original content.
4. Use direct, conversational language and include hook and call to action.
5. The script should sound natural when read aloud.
6. Each reel should be completely independent and self-contained.
7. WRITE EVERYTHING IN RUSSIAN LANGUAGE.

REQUIRED OUTPUT FORMAT:
Your response should be in JSON format with these fields:
- "heygen_script": The complete script text to be spoken by the avatar in Russian, without any stage directions or formatting
- "title": A catchy, attention-grabbing title for the reel (40-60 characters) to use in thumbnails
- "hashtags": 5-7 relevant hashtags in Russian
- "description": A compelling, informative description that summarizes what the video is about (not just title). This should be a marketing description that makes viewers want to watch (150-200 characters)

Return ONLY valid JSON without any additional explanation.
"""

# System prompt for reel generation
# Used in: src/platforms/workflow/create_reel_scripts.py -> ReelGenerator.generate_reel_script() method
REEL_GENERATION_SYSTEM_PROMPT = "You are an expert reel script creator that transforms educational content into engaging, shareable Instagram reels. You always respond with valid JSON. IMPORTANT: You must respond ONLY in Russian language."


# 3. Viral Potential Analysis Prompt
# Used in: src/platforms/workflow/reel_picker.py -> analyze_viral_potential() function
# Purpose: Analyze and score reel scripts for viral potential
VIRAL_ANALYSIS_PROMPT = """
You are a retention optimization specialist for short-form video content.

Analyze this reel content and rate its retention potential (likelihood viewers will watch to the end) on a scale of 1-10:

{title}
{description}
{heygen_script}
Tags: {hashtags}

Frame your analysis around these retention factors:
- Hook strength (first 3 seconds grab attention)
- Story arc (maintains curiosity throughout)
- Pacing (no slow moments that cause drop-off)
- Promise fulfillment (delivers on hook's promise)
- Length optimization (content is tight, no fluff)
- Call-to-action timing (placed at peak engagement)

Return a JSON object:
{{
  "score": [1-10 integer],
  "explanation": [why viewers will/won't stay to the end],
  "improvement_insight": [specific suggestion to increase retention]
}}
"""

# System prompt for viral analysis
# Used in: src/platforms/workflow/reel_picker.py -> analyze_viral_potential() function
VIRAL_ANALYSIS_SYSTEM_PROMPT = "You analyze social media content and predict its viral potential. Respond only with JSON."


# 4. Final Reel Editing Prompt
# Used in: src/platforms/workflow/integration.py -> final_reel_editing() function
# Purpose: Improve engagement in selected reels
FINAL_EDITING_PROMPT = """Edit this Instagram reel script to make it more engaging and viral. 

CURRENT SCRIPT:
{script}

TITLE:
{title}

EDITING GUIDELINES:
{edit_prompt}

For this specific reel, use the following hook style:
{hook_variant}

Return ONLY the edited script text without any explanation or additional formatting. The script should be ready to use as-is and in Russian language.
"""

# System prompt for final editing
# Used in: src/platforms/workflow/integration.py -> final_reel_editing() function
FINAL_EDITING_SYSTEM_PROMPT = "You are an expert at editing social media scripts to maximize engagement. Make edits according to the guidelines provided, while preserving the core message and educational value."


# 5. Default Edit Guidelines
# Used in: src/platforms/workflow/integration.py -> process_google_doc_to_reels() function
# Purpose: Define rules for improving reel engagement
DEFAULT_EDIT_GUIDELINES = """Убрать: 
    - Приветствие (добрый день, привет, и т.д.)
    - Представления эксперта (я Сергей Черненко)
    - Фразы типа «вот про это мы поговорим в следующем ролике»

    Добавить:
    - Начать с одного из вариантов цепляющего вступления:
      * «Это видео для тех, кто...» (например: хочет научиться монтировать, но не знает, с чего начать)
      * «Это история о том, как...» (например: я сделал вирусное видео, даже не зная, как монтировать)
      * «А вы знали, что...» (например: можно монтировать видео бесплатно на профессиональном уровне)
      * «Вряд ли вы мне поверите, но...» (например: раньше я боялся монтировать, потому что думал, что это сложно)
      * «У меня ушло несколько лет, чтобы...» (например: понять, как сделать видео, которые набирают миллионы просмотров)
      * Начать со слова «короче» - посыл "сейчас я быстро расскажу"
      * Использовать фразы с превосходными прилагательными: "Самый классный в мире...", "Самый провальный...", "Самый лучший...", "Самый быстрый...", "Самый неэффективный способ..."

    Сохранить:
    - Основное образовательное содержание
    - Ключевые тезисы и рекомендации
    - Призыв к действию в конце"""


# 6. Hook Variations
# Used in: src/platforms/workflow/integration.py -> final_reel_editing() function
# Purpose: Provide different hook styles to use in final editing (selected randomly for each reel)
HOOK_VARIATIONS = [
    "Это видео для тех, кто...",
    "Это история о том, как...",
    "А вы знали, что...",
    "Вряд ли вы мне поверите, но...",
    "У меня ушло несколько лет, чтобы...",
    "Короче...",
    "Самый классный в мире...",
    "Самый провальный...",
    "Самый лучший...",
    "Самый быстрый...",
    "Самый неэффективный способ...",
    "Это мой самый лучший *ваша экспертность* лайфхак!",
    "Сейчас за 1 минуту я тебе расскажу *боль ца*",
    "Худшее, что можно сделать после *точка Б для ЦА*",
    "Самый простой способ…",
    "А ты знала, что…?",
    "Самый вредный совет…",
    "Развеиваю 10 мифов про *ваша ниша* за 1 минуту",
    "Хочешь это? Делай это!",
    "Это единственное, что вам нужно знать, чтобы *точка Б ЦА*",
    "Всратые советы в *ваша ниша*",
    "Если *возражение ЦА*, но *идеальная точка Б ЦА* хочется, то…",
    "Секрет *ваша ниша*, который *точка Б*",
    "3 секретные фишки, которые приведут к *идеальная точка Б клиента*",
    "Если ты не будешь делать *верное действие ЦА*, то ты не получишь *идеальная точка Б ЦА*",
    "Смотри как легко и быстро можно избавиться от *боль ЦА*",
    "Если ты *действие ца*, то тебе стоит делать *лайфхак для ца*",
    "Короче, рассказываю самый ленивый способ *проблема ЦА*",
    "Тебе точно надо сделать скриншот, если ты хочешь *идеальная точка б ца*",
    "Как *боль*, чтобы *точка Б*",
    "Худшая *ошибка ЦА*",
    "Как за одно действие…",
    "Перестань уже *самая распространенная ошибка ЦА*!",
    "Как за одно действие…",
    "Самый большой секрет про...",
    "Тебя тоже бесит *боль ЦА?*",
    "Обязательно сделай … если хочешь *точка Б*",
    "3 закона про *ваша ниша*, с которыми ты не согласишься",
    "Итак, готовься скринить, сейчас я тебе расскажу как решить *боль ца*",
    "Не делай *действие ца* пока не сделаешь это…",
    "Знаете, что в *ваша ниша* бесит больше всего?",
    "1/2/3/4/5 закон *идеальная точка Б*",
    "Читерский способ как *точка б*"
]