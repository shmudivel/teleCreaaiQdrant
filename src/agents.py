from textwrap import dedent
from crewai import Agent
from .vector_db_tool import VectorDBToolset

class contentSocialMediaAgents():
    def general_content_social_media_agent(self):
      vdb_tools = VectorDBToolset()
      return Agent(
        role="Главный редактор социальных медиа",
        goal='Задача чтоб текст был понятен и интересен целевой аудитории и людям которые будут читать стало интересно еще что-то почитать у Сергея Черненко',
        tools=vdb_tools.tools(), 
        backstory=dedent("""\
          Вы - главный редактор социальных медиа. Ваша задача - создать текст, который будет понятен и интересен целевой аудитории, а также привлечет внимание к Сергею Черненко.
"""),
        verbose=True
      )
      
    def editor_social_media_agent(self):
      vdb_tools = VectorDBToolset()
      return Agent(
        role='Редактор социальных медиа',
        goal='Твоя цель чтоб текст соответвовал целевой аудитории, и соответствовал стандартам социальных сетей',
        tools=vdb_tools.tools(),
        backstory=dedent("""\
          Вы специалист по социальным медиа. Ваша задача - провести тщательную редактуру поста для социальных сетей. На основе текста, скрипта для видео на YouTube и целевой аудитории.
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