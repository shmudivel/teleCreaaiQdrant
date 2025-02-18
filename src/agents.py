from textwrap import dedent
from crewai import Agent
from .vector_db_tool import VectorDBToolset

class contentSocialMediaAgents():
    def general_content_social_media_agent(self):
      vdb_tools = VectorDBToolset()
      return Agent(
        role="Специалист по коммуникациям",
        goal='Создавать трёхчастные ответы: реакция на комментарий, полезная информация, призыв подписаться на телеграм канал t.me/corphacker ',
        tools=vdb_tools.tools(), 
        backstory=dedent("""\
                Вы — опытный специалист по деловым коммуникациям. 
                Ваша задача:
                  • Соблюдать трёхблочную структуру ответа
                  • Подбирать релевантные факты из базы знаний
                  • Следить за длиной ответа"""),
        verbose=True
      )
      
    def editor_social_media_agent(self):
      vdb_tools = VectorDBToolset()
      return Agent(
        role='Редактор комментариев',
        goal='Контроль структуры и длины ответа, адаптация под формат соцсети, призыв подписаться на телеграм канал t.me/corphacker',
        tools=vdb_tools.tools(),
        backstory=dedent("""\
                Вы — эксперт по деловой коммуникации. 
                Ваша задача:
                  • Проверять соблюдение трёхблочной структуры
                  • Сравнивать длину ответа с исходным комментарием
                  • Адаптировать стиль под конкретную соцсеть"""),
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