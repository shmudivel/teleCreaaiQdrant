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
2. MAKE THE SCRIPT ENGAGING, CONCISE, AND SUITABLE FOR AN INSTAGRAM REEL (30-50 SECONDS).
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

Also include this call-to-action at the end (Depending on the topic and tone of the video, add one emotional, one rational, and one light call-to-action. Avoid repeating phrases from the video word for word.):
{call_to_action_variant}

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




# 7. HeyGen Script Optimization Prompt
# Used in: src/platforms/workflow/integration.py -> optimize_heygen_script() function
# Purpose: Optimize script for natural voice delivery by HeyGen avatar (improving natural flow and pacing)
HEYGEN_OPTIMIZATION_PROMPT = """Ты — эксперт-редактор сценариев для озвучивания в Elevenlabs.io.
Перепиши предоставленный текст так, чтобы он звучал максимально естественно при озвучивании, и раздели его на 4 равные части для разных камер.

ВАЖНО: СОХРАНЯЙ РУССКИЙ ЯЗЫК В ТЕКСТЕ. НЕ ПЕРЕВОДИ НА АНГЛИЙСКИЙ. ВЕСЬ ТЕКСТ ДОЛЖЕН ОСТАВАТЬСЯ НА РУССКОМ ЯЗЫКЕ.
ВАЖНО: ИСПОЛЬЗУЙ ТОЛЬКО ТЕГИ <speak>, <break>, И НИКАКИХ ДРУГИХ XML-ПОДОБНЫХ КОНСТРУКЦИЙ.
ВАЖНО: НИКАКИХ ОБЫЧНЫХ ПЕРЕВОДОВ СТРОК ('\n') ВНУТРИ ТЕГОВ <speak>! ТЕКСТ ДОЛЖЕН БЫТЬ СПЛОШНЫМ ВНУТРИ ТЕГОВ.

Правила форматирования:
1. Раздели сценарий на 4 примерно равные части, и каждую часть оформи отдельным блоком: 
   <!-- CAM‑1 -->
   <speak>
   Текст первой части
   </speak>
   <!-- CAM‑2 -->
   <speak>
   Текст второй части
   </speak>
   и так далее.

2. Используй тег <break time="0.4s"/> для коротких пауз, <break time="0.6s"/> для средних пауз, <break time="0.8s"/> для длинных пауз.

3. Разговорный стиль
   • Каждое предложение ≤ 20 слов, не больше двух запятых.
   • Одна мысль — одно предложение.

4. Естественные паузы
   • Добавляй <break> между логическими частями речи.
   • После важных утверждений ставь паузы длиннее.
   • Перед введением новой мысли добавляй паузу.

5. Акценты и ударения
   • Важные слова ставь в начало или конец предложения.
   • Используй повторения для усиления важных идей.

6. Цифры, аббревиатуры
   • Числа прописью, если важно ударение («двенадцать»).
   • ВСЕ АББРЕВИАТУРЫ ДОЛЖНЫ БЫТЬ ПОЛНОСТЬЮ РАСПИСАНЫ ТЕКСТОМ, БЕЗ СОКРАЩЕНИЙ (НАПРИМЕР, «ИСКУССТВЕННЫЙ ИНТЕЛЛЕКТ» ВМЕСТО «ИИ»).

7. Структурирование контента:
   • В CAM-1: Размести hook и введение в тему.
   • В CAM-2: Размести первую часть основного контента.
   • В CAM-3: Размести вторую часть основного контента.
   • В CAM-4: Размести заключение и call-to-action.

ВХОДЯЩИЙ ТЕКСТ:
{script}

Отдай результат в виде структурированного текста с 4 блоками для разных камер, разделенными маркерами <!-- CAM‑X -->, каждый блок внутри тегов <speak></speak>. Текст внутри тегов должен быть сплошным, без переводов строк.
"""

# System prompt for HeyGen optimization
# Used in: src/platforms/workflow/integration.py -> optimize_heygen_script() function
HEYGEN_OPTIMIZATION_SYSTEM_PROMPT = "Ты эксперт по редактированию сценариев для синтеза речи на русском языке в Elevenlabs.io. Твоя задача - оптимизировать русский текст для естественного звучания, разделив его на 4 части для разных камер. Используй только теги <speak> и <break>. Не используй обычные переводы строк внутри тегов <speak>. Текст внутри тегов <speak> должен быть сплошным. Сохраняй русский язык текста. Структурируй выходные данные в формате: <!-- CAM‑1 --> <speak>текст</speak> <!-- CAM‑2 --> <speak>текст</speak> и т.д."


# 8. Script Validation Prompt
# Used in: src/platforms/workflow/integration.py -> validate_heygen_script() function
# Purpose: Check and fix scripts to ensure they comply with all HeyGen rules
SCRIPT_VALIDATION_PROMPT = """Проверь и исправь этот сценарий для HeyGen аватара. Вот критерии качества:

1. Hook (первая фраза): проверь, соответствует ли начальная фраза сценария одному из шаблонов:
{hook_examples}
... и другие подобные шаблоны.

2. Call-to-action (последняя фраза): проверь, есть ли призыв к действию в конце сценария, например:
- Подпишись, чтобы не пропустить ещё больше полезных советов
- Хочешь больше таких идей? Жми «подписаться»
- Напиши в комментариях, что тебе откликается
... и другие подобные призывы к действию.

3. Правила оптимизации для текста:
   • Каждое предложение ≤ 20 слов
   • Не более 2 запятых в предложении
   • Никаких многоточий (...)
   • Важные числа написаны прописью (например, "пять" вместо "5")
   • При первом упоминании аббревиатур дается расшифровка: "искусственный интеллект (ИИ)"

4. Если hook не соответствует шаблонам, переформулируй первое предложение, чтобы оно четко соответствовало одному из шаблонов.

5. Если call-to-action отсутствует, добавь подходящий призыв к действию в конце сценария.

6. Предложения длиннее 20 слов разбей на более короткие.

7. Предложения с более чем 2 запятыми переформулируй или раздели.

ОЧЕНЬ ВАЖНО:
- УДАЛИ ВСЕ ДВОЙНЫЕ ПЕРЕВОДЫ СТРОКИ ('\n\n')! ТЕКСТ ДОЛЖЕН БЫТЬ СПЛОШНЫМ БЕЗ РАЗРЫВОВ СТРОК!
- УДАЛИ ВСЕ КАВЫЧКИ ('"')!

НАЗВАНИЕ: {title}

ТЕКУЩИЙ СЦЕНАРИЙ:
{script}

Исправь и верни ТОЛЬКО текст сценария без объяснений или комментариев. Текст должен остаться на русском языке.
"""

# System prompt for script validation
# Used in: src/platforms/workflow/integration.py -> validate_heygen_script() function
SCRIPT_VALIDATION_SYSTEM_PROMPT = "Ты эксперт по проверке и улучшению сценариев для аватара HeyGen. Твоя задача — проверить сценарий на соответствие правилам и исправить все нарушения, включая удаление двойных переводов строк и кавычек. Делаешь это тщательно, следуя всем критериям. Твой ответ должен содержать ТОЛЬКО исправленный текст сценария на русском языке, без объяснений или дополнительных комментариев и без разрывов строк."


# 9. Number to Word Conversion Prompt
# Used in: src/platforms/workflow/integration.py -> convert_numbers_to_words() function
# Purpose: Convert all numbers in the script to their word representation in Russian
NUMBER_CONVERSION_PROMPT = """Перепиши текст сценария, заменив ВСЕ числа на их словесное написание на русском языке.

Правила замены:
1. Замени все цифры на слова: "5" → "пять", "42" → "сорок два" и т.д.
2. Для годов используй правильное словесное выражение: "2025 год" → "две тысячи двадцать пятый год"
3. Для времени используй словесное выражение: "5 минут" → "пять минут"
4. Для денежных сумм пиши словами: "$20" → "двадцать долларов"
5. Дроби пиши словами: "1.5" → "одна целая пять десятых"
6. Замени все числительные, даже если они уже записаны словами, чтобы убедиться в корректности записи
7. Числа в составе аббревиатур и названий моделей (GPT-4, T1000) оставь как есть

ОЧЕНЬ ВАЖНО:
- УДАЛИ ВСЕ ДВОЙНЫЕ ПЕРЕВОДЫ СТРОКИ ('\n\n')! ТЕКСТ ДОЛЖЕН БЫТЬ СПЛОШНЫМ БЕЗ РАЗРЫВОВ СТРОК! 
- УДАЛИ ВСЕ КАВЫЧКИ ('"')!
- СОХРАНИ ВЕСЬ ОСТАЛЬНОЙ ТЕКСТ БЕЗ ИЗМЕНЕНИЙ! РАБОТАЙ ТОЛЬКО С ЧИСЛАМИ И УКАЗАННЫМИ ВЫШЕ СИМВОЛАМИ!

ТЕКУЩИЙ СЦЕНАРИЙ:
{script}

Верни ТОЛЬКО текст с заменёнными числами на русском языке без объяснений.
"""

# System prompt for number conversion
# Used in: src/platforms/workflow/integration.py -> convert_numbers_to_words() function
NUMBER_CONVERSION_SYSTEM_PROMPT = "Ты эксперт по переписыванию текстов для озвучивания на русском языке. Твоя задача — заменить все числа на их словесное выражение, удалить двойные переводы строк и кавычки для естественного звучания при озвучивании. Возвращай только переработанный текст без пояснений и без разрывов строк."

CALL_TO_ACTION_VARIATIONS = [
    "Подпишись, чтобы не пропустить ещё больше полезных советов",
    "Подпишись, если хочешь делать карьеру осознанно",
    "Хочешь больше таких идей? Жми «подписаться»",
    "Это только начало — дальше интереснее",
    "Подписывайся, если устал от воды и хочешь по делу",
    "Подписка = доступ к новым ролям, деньгам и возможностям",
    "Напиши в комментариях, что тебе откликается",
    "А у тебя было такое? Напиши в комментариях",
    "Какая мысль зацепила — делись ниже",
    "Пробовал ли ты это уже? Ждём твой опыт",
    "Согласен или не согласен — напиши",
    "Один комментарий может изменить чью-то карьеру",
    "Хочешь больше таких разборов? Жми «Сохранить»",
    "Сохрани, чтобы не забыть перед важной встречей",
    "Этот совет пригодится — не потеряй",
    "Сделай скрин и вернись к этому перед собеседованием",
    "Сохрани, чтобы поделиться с командой",
    "Используй это как чек-лист — не забудь вернуться",
    "Смотри полную версию видео по ссылке в описании",
    "Полное видео — в описании под роликом",
    "Хочешь примеры и шаблоны? Ссылка в шапке профиля",
    "Регистрируйся на бесплатные уроки",
    "Подробнее — на сайте, ссылка под видео",
    "Вся система — в видео на YouTube",
    "Переходи в шапку профиля — там чек-лист",
    "Зарегистрируйся на бесплатные видеоуроки — ссылка в описании",
    "Поделись с другом, которому это актуально",
    "Прямо сейчас задай этот вопрос своему ИИ — и посмотри, что он ответит",
    "Не теряй — пересмотри, когда будет сложный разговор с начальством",
    "Этот совет спасает карьеру — не забудь подписаться",
    "Подпишись, если хочешь расти быстрее, чем другие"
]
