from textwrap import dedent
from crewai import Agent
from .vector_db_tool import VectorDBToolset

class contentSocialMediaAgents():
    def content_adaptation_agent(self):
        vdb_tools = VectorDBToolset()
        return Agent(
            role="Специалист по адаптации контента",
            goal='Адаптировать YouTube-контент для различных платформ',
            tools=vdb_tools.tools(),
            backstory=dedent("""\
                Вы — эксперт по адаптации контента для разных платформ.
                Ваша задача:
                  • Анализировать исходный YouTube-контент
                  • Выделять ключевые моменты и тезисы
                  • Структурировать информацию для разных форматов"""),
            verbose=True
        )
      
    def dzen_specialist_agent(self):
        vdb_tools = VectorDBToolset()
        return Agent(
            role='Редактор Дзен',
            goal='Создать engaging пост для платформы Дзен',
            tools=vdb_tools.tools(),
            backstory=dedent("""\
                Вы — эксперт по созданию контента для Дзен. 
                Ваша задача:
                  • Создавать захватывающие заголовки
                  • Адаптировать стиль под аудиторию Дзен
                  • Добавлять призывы к действию
                  • Оптимизировать текст под SEO Дзена"""),
            verbose=True
        )

    def vc_specialist_agent(self):
        vdb_tools = VectorDBToolset()
        return Agent(
            role='Редактор VC.ru',
            goal='Создать профессиональный пост для VC.ru',
            tools=vdb_tools.tools(),
            backstory=dedent("""\
                Вы — эксперт по бизнес-контенту для VC.ru.
                Ваша задача:
                  • Фокусироваться на бизнес-аспектах
                  • Использовать профессиональный стиль
                  • Структурировать текст для удобного чтения
                  • Добавлять релевантные подзаголовки"""),
            verbose=True
        )