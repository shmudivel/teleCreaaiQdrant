from textwrap import dedent
from crewai import Agent
from .vector_db_tool import VectorDBToolset

class SocialMediaAgent():
    def content_creator_agent(self):
        vdb_tools = VectorDBToolset()
        return Agent(
            role="редактор контента для dzen.ru",
            goal='редактировать только часть 1 из 4 частей контента',
            tools=vdb_tools.tools(),
            backstory=dedent("""\
                
                Ваши задачи:
                • редактирует и четко  идет по заданию
                • оставляю колличество предложений как в оригинальном тексте
                 """),
            verbose=True
        )