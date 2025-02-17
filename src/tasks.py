from textwrap import dedent
from crewai import Task


class contentSocialMediaTasks():


  def research_task(self, agent, original_comment, social_platform):
    return Task(
      description=dedent(f"""\
            Создание ответа на комментарий в соцсети:

            1. Анализ комментария
            - Определите основную тему и контекст
            - Найдите ключевые моменты для ответа
            - Подготовьте полезную информацию по теме

            2. Структура ответа
            - Начните с вежливого обращения
            - Выразите понимание позиции собеседника
            - Предоставьте полезную информацию (4-5 предложений)
            - Подкрепите ответ фактами или примерами

            3. Стиль общения
            - Используйте деловой, но дружелюбный стиль
            - Сохраняйте уважительный тон
            - Избегайте просторечий и сленга
            - Пишите информативно и по существу

            Исходный комментарий: {original_comment}
            Платформа: {social_platform}"""),
      expected_output=dedent(f"""\
        Информативный, вежливый ответ с полезными данными."""),
      agent=agent,
      async_execution=False
    )
    
  def industry_analysis_task(self, agent, original_comment, social_platform):
    return Task(
      description=dedent(f"""\
            Финальная доработка ответа на комментарий:

            1. Проверка соответствия платформе
            - Учтите особенности общения в {social_platform}
            - Проверьте уместность эмоджи и сленга
            - Убедитесь, что длина ответа оптимальна

            2. Тон и подача
            - Сделайте ответ личным и искренним
            - Избегайте формального тона
            - Добавьте живые разговорные элементы
            - Проверьте эмоциональный баланс

            3. Завершающие штрихи
            - Проверьте грамотность и читаемость
            - Сохраните краткость (максимум 4-5 предложения)

            Исходный комментарий: {original_comment}
            Платформа: {social_platform}"""),
      expected_output=dedent("""\
        Готовый к публикации ответ, соответствующий формату выбранной соцсети."""),
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