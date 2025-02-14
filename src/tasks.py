from textwrap import dedent
from crewai import Task


class contentSocialMediaTasks():


  def research_task(self, agent, text_context_script_video_youtube, target_audience):
    return Task(
      description=dedent(f"""\
            1. Заголовок (Title)
            Напишите цепляющий и интригующий заголовок статьи, который сразу привлечёт внимание читателя на vc.ru.

            2. Введение (Hook)
            - Используйте первую часть текста, чтобы «зацепить» читателя с первых строк: краткая история, мощный факт или интригующий вопрос.
            - Объясните, почему эта тема актуальна именно сейчас, и как она поможет читателю.

            3. Основная часть (Main Body)
            - Структурируйте текст на логичные блоки, разбавляйте их подзаголовками.
            - Используйте примеры, истории из жизни и практические кейсы, чтобы проиллюстрировать ключевые моменты.
            - Если речь идёт о карьере и отношениях с руководителем, опишите типичные ошибки и способы их избежать.
            - Покажите пошаговые рекомендации или «чек-лист»: читателям важно понимать, что именно они могут предпринять прямо сейчас.

            4. Заключение (Summary)
            - Подведите итоги и ещё раз акцентируйте внимание на главной мысли.
            - Дайте небольшую «затравку» на дальнейшее развитие темы или пообещайте дополнительный материал в будущем.

            5. Призыв к действию (Call to Action)
            - Пригласите читателей обсудить тему в комментариях на vc.ru.
            - Предложите подписаться на ваш профиль, рассказать о своих кейсах или задать вопросы.
            - Уточните, что они могут найти больше информации (например, в ваших предыдущих статьях или видео).

            6. Тон и стиль (Tone & Style)
            - Пишите с пониманием и эмпатией к читателю.
            - Держите баланс между информативностью и лёгкой подачей.
            - Избегайте чрезмерно сложного языка, но сохраняйте экспертность.

        Контекст видео: {text_context_script_video_youtube}
        Целевая аудитория: {target_audience}"""),
      expected_output=dedent(f"""\
        Развернутый текст, соответствующий целевой аудитории vc.ru и стандартам соцсетей."""),
      agent=agent,
      async_execution=False
    )
    
  def industry_analysis_task(self, agent, text_context_script_video_youtube, target_audience):

    return Task(
      description=dedent(f"""\
            1. Заголовок (Title)
            - Придумайте короткий, интригующий заголовок, который сразу привлечёт внимание аудитории dzen.ru.

            2. Вступление (Intro / Лид)
            - Начните с мощного тезиса, личной истории или неожиданного факта, чтобы «зацепить» читателя.
            - Укажите, почему эта тема важна: как она поможет в карьере, в личной жизни, саморазвитии и т.д.
            - Старайтесь писать короткими абзацами: на dzen.ru обычно лучше воспринимаются лаконичные тексты.

            3. Основная часть (Main Body)
            - Разбейте материал на логичные блоки или подзаголовки (2–4 основных пункта).
            - Используйте реальные истории и примеры (как кейс со «Сбером» или история про упущенные возможности).
            - Подчеркните ключевые выводы из этих примеров: например, важность навыков коммуникации или нетворкинга.
            - Включайте практические рекомендации: что читатель может сделать прямо сейчас, чтобы улучшить свою ситуацию.

            4. Заключение (Summary)
            - Подведите итоги: повторите самую главную идею — почему навыки коммуникации (или другая заявленная тема) критичны для роста и развития.
            - Сделайте аккуратную «завязку» на возможное продолжение темы (например, анонс курса, предстоящие материалы, новую статью).

            5. Призыв к действию (Call to Action)
            - Предложите подписаться на ваш канал на dzen.ru, поделиться статьёй в социальных сетях или задать вопросы в комментариях.
            - Можете упомянуть грядущие события, новые материалы, курсы или видео. Главное — сохранить дружелюбный и неагрессивный тон.

            6. Тональность и особенности dzen.ru
            - Используйте эмпатичный, доброжелательный стиль общения.
            - Пишите чётко и понятно, избегайте излишне длинных абзацев — читатели dzen.ru ценят структурированные и «лёгкие» для восприятия тексты.
            - При необходимости добавляйте изображения, иллюстрации или скриншоты (в зависимости от функционала платформы).

        Контекст: {text_context_script_video_youtube}
        Целевая аудитория: {target_audience}"""),
      expected_output=dedent("""\
        Развернутый, структурированный текст для dzen.ru, отражающий указанный контекст и ориентированный на заданную целевую аудиторию."""),
      async_execution=True,
      agent=agent
    )
    
#   def meeting_strategy_task(self, agent, meeting_context, meeting_objective):
#     return Task(
# 			description=dedent(f"""\
# 				Develop strategic talking points, questions, and discussion angles
# 				for the meeting based on the research and industry analysis conducted

# 				Meeting Context: {meeting_context}
# 				Meeting Objective: {meeting_objective}"""),
# 			expected_output=dedent("""\
# 				Complete report with a list of key talking points, strategic questions
# 				to ask to help achieve the meetings objective during the meeting."""),
# 			agent=agent
# 		)
    
#   def summary_and_briefing_task(self, agent, meeting_context, meeting_objective):
#     return Task(
# 			description=dedent(f"""\
# 				Compile all the research findings, industry analysis, and strategic
# 				talking points into a concise, comprehensive briefing document for
# 				the meeting.
# 				Ensure the briefing is easy to digest and equips the meeting
# 				participants with all necessary information and strategies.

# 				Meeting Context: {meeting_context}
# 				Meeting Objective: {meeting_objective}"""),
# 			expected_output=dedent("""\
# 				A well-structured briefing document that includes sections for
# 				participant bios, industry overview, talking points, and
# 				strategic recommendations."""),
# 			agent=agent
# 		)