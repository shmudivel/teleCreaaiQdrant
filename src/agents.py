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
    
    def content_creator_agent_part2(self):
        vdb_tools = VectorDBToolset()
        return Agent(
            role="редактор контента для dzen.ru",
            goal='редактировать только часть 2 из 4 частей контента',
            tools=vdb_tools.tools(),
            backstory=dedent("""\
                
                Ваши задачи:
                • редактирует и четко идет по заданию
                • оставляю колличество предложений как в оригинальном тексте
                • работает только с частью 2
                 """),
            verbose=True
        )
    
    def content_creator_agent_part3(self):
        vdb_tools = VectorDBToolset()
        return Agent(
            role="редактор контента для dzen.ru",
            goal='редактировать только часть 3 из 4 частей контента',
            tools=vdb_tools.tools(),
            backstory=dedent("""\
                
                Ваши задачи:
                • редактирует и четко идет по заданию
                • оставляю колличество предложений как в оригинальном тексте
                • работает только с частью 3
                 """),
            verbose=True
        )
    
    def content_creator_agent_part4(self):
        vdb_tools = VectorDBToolset()
        return Agent(
            role="редактор контента для dzen.ru",
            goal='редактировать только часть 4 из 4 частей контента',
            tools=vdb_tools.tools(),
            backstory=dedent("""\
                
                Ваши задачи:
                • редактирует и четко идет по заданию
                • оставляю колличество предложений как в оригинальном тексте
                • работает только с частью 4
                 """),
            verbose=True
        )