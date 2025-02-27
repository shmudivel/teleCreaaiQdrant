from textwrap import dedent
from crewai import Agent
from .vector_db_tool import VectorDBToolset

class SocialMediaAgent():
    def content_creator_agent(self):
        vdb_tools = VectorDBToolset()
        return Agent(
            role="Универсальный создатель контента",
            goal='Создавать качественный контент для социальных сетей',
            tools=vdb_tools.tools(),
            backstory=dedent("""\
                Вы — эксперт по созданию контента для различных платформ.
                Ваши задачи:
                • Анализировать исходный контент
                • Адаптировать стиль под целевую платформу
                • Добавлять релевантные данные из базы знаний
                • Сохранять основную идею контента"""),
            verbose=True
        )