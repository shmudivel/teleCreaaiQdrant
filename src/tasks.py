from textwrap import dedent
from crewai import Task


class contentSocialMediaTasks():


  def research_task(self, agent, original_comment, social_platform):
    return Task(
      description=dedent(f"""\
            Создание ответа на комментарий в соцсети:

            1. Адресация комментария
            - Вежливо отреагируйте на основной посыл
            - Покажите понимание позиции автора
            - Сформулируйте ясный ответ на вопрос/проблему

            2. Полезная информация
            - Приведите 1-2 ключевых факта из базы знаний
            - Используйте конкретные примеры или данные
            - Сохраняйте информативность и краткость

            3. Призыв к действию
            - упоменуть что ссылка на телеграм канал t.me/corphacker
            - Используйте естественную, ненавязчивую форму

            Ограничения:
            - Ответ не должен быть длиннее исходного комментария
            - Избегайте маркетинговых формулировок

            Исходный комментарий: {original_comment}
            Платформа: {social_platform}"""),
      expected_output=dedent(f"""\
        Ответ из трёх логических блоков, заканчивающийся призывом подписаться.
        Максимальная длина: {len(original_comment.split())} слов."""),
      agent=agent,
      async_execution=False
    )
    
  def industry_analysis_task(self, agent, original_comment, social_platform):
    return Task(
      description=dedent(f"""\
            Финальная доработка ответа:
            
            1. Проверка структуры
            - Соответствие трёхблочной структуре
            - Наличие полезной информации из базы
            - Естественный призыв к подписке
            
            2. Контроль длины
            - Сравнение длины с исходным комментарием
            - Сокращение при превышении длины
            - Удаление избыточных формулировок

            3. Адаптация под платформу
            - Проверка уместности стиля для {social_platform}

            Исходный комментарий: {original_comment}"""),
      expected_output=dedent("""\
        Краткий ответ, соответствующий требованиям платформы и 
        не превышающий длину исходного комментария."""),
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