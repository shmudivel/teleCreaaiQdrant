from textwrap import dedent
from crewai import Task


class contentSocialMediaTasks():


  def research_task(self, agent, text_context_script_video_youtube, target_audience):
    return Task(
      description=dedent(f"""\
        Твоя задача - написать текст, который будет соответствовать всем требованиям telegram канал пост. 
        Текст должен быть интересным и увлекательным, чтобы привлечь внимание читателей и вызвать у них желание узнать больше об авторе поста.
        Учитывай следующие моменты:
        - Заголовок должен быть цепляющим и интригующим.
        - Введение должно захватывать внимание с первых строк.
        - Основная часть текста должна быть структурированной и содержательной.
        - Используй примеры и истории для иллюстрации ключевых моментов.
        - Заключение должно подводить итог и побуждать к дальнейшему взаимодействию с автором.
        - но при всем это текст должен быть с пониманием и эмпатией  

        Контекст видео: {text_context_script_video_youtube}
        Целевая аудитория: {target_audience}"""),
      expected_output=dedent(f"""\
        Развернутый текст, который соответствует целевой аудитории и стандартам социальных сетей"""),
      agent=agent,
      async_execution=False
    )
    
  def industry_analysis_task(self, agent, text_context_script_video_youtube, target_audience):

    return Task(
      description=dedent(f"""\
        На основе контекста, скрипта для видео на YouTube и целевой аудитории, проведите глубокий анализ и напишите пост для telegram канал пост.
        Текст должен быть понятен и интересен целевой аудитории и людям которые захотят узнать больше о теме на ютубе.

        Контекст: {text_context_script_video_youtube}
        Целевая аудитория: {target_audience}"""),
      expected_output=dedent("""\
        Детальный анализ трендов, проблем и возможностей, с практическими рекомендациями 
        для целевой аудитории."""),
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