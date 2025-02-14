from textwrap import dedent
from crewai import Agent
from .vector_db_tool import VectorDBToolset

class contentSocialMediaAgents():
    def general_content_social_media_agent(self):
      vdb_tools = VectorDBToolset()
      return Agent(
        role="Главный редактор социальных медиа",
        goal='Создать текст, который будет понятен и интересен целевой аудитории, а также привлечёт внимание к Сергею Черненко. Лёгкость восприятия, дружелюбный тон и чёткую структуру.',
        tools=vdb_tools.tools(), 
        backstory=dedent("""\
                Вы — главный редактор социальных медиа. 
                Ваша задача:
                  • Создать текст, интересный для читателей.
                  • Уделить особое внимание коротким абзацам, цепляющим заголовкам и дружелюбному стилю.
                  • Стимулировать интерес к личности Сергея Черненко и мотивировать читателей узнавать о нём больше.
"""),
        verbose=True
      )
      
    def editor_social_media_agent(self):
      vdb_tools = VectorDBToolset()
      return Agent(
        role='Редактор социальных медиа',
        goal='Сделать так, чтобы текст соответствовал целевой аудитории dzen.ru и отвечал стандартам социальных сетей (короткие абзацы, актуальные примеры, призыв к взаимодействию).',
        tools=vdb_tools.tools(),
        backstory=dedent("""\
                Вы — специалист по социальным медиа. 
                Ваша задача:
                  • Провести тщательную редактуру поста.
                  • Учесть специфику формата: 
                    - Структурированное изложение (заголовок, вступление, основная часть, итог, призыв к действию).
                    - Тон и стиль: дружелюбный, но при этом экспертный.
                  • Помочь автору (Сергею Черненко) выглядеть профессионально и заинтересовать аудиторию своим контентом.
"""),
        verbose=True
      )
      
    # def meeting_strategy_agent(self):
    #   return Agent(
    #     role='Meeting Strategy Advisor',
    #     goal='Develop talking points, questions, and strategic angles for the meeting',
    #     backstory=dedent("""\
    #         As a Strategy Advisor, your expertise will guide the development of
    #         talking points, insightful questions, and strategic angles
    #         to ensure the meeting's objectives are achieved."""),
    #     verbose=True
    #   )
      
    # def summary_and_briefing_agent(self): 
    #   return Agent(
    #     role='Briefing Coordinator',
    #     goal='Compile all gathered information into a concise, informative briefing document',
    #     backstory=dedent("""\
    #         As the Briefing Coordinator, your role is to consolidate the research,
    #         analysis, and strategic insights."""),
    #     verbose=True
    #   )