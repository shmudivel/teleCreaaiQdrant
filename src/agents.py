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
                Я профессиональный редактор контента для dzen.ru.

                Ваши задачи:
                • редактирует и четко идти по заданию
                • ОСТАВЛЯЮ КОЛИЧЕСТВО ПРЕДЛОЖЕНИЙ КАК В ОРИГИНАЛЬНОМ ТЕКСТЕ
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
                Я профессиональный редактор контента для dzen.ru.

                Ваши задачи:
                • редактирует и четко идти по заданию
                • ОСТАВЛЯЮ КОЛИЧЕСТВО ПРЕДЛОЖЕНИЙ КАК В ОРИГИНАЛЬНОМ ТЕКСТЕ
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
                Я профессиональный редактор контента для dzen.ru.

                Ваши задачи:
                • редактирует и четко идти по заданию
                • ОСТАВЛЯЮ КОЛИЧЕСТВО ПРЕДЛОЖЕНИЙ КАК В ОРИГИНАЛЬНОМ ТЕКСТЕ
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
                Я профессиональный редактор контента для dzen.ru.

                Ваши задачи:
                • редактирует и четко идти по заданию
                • ОСТАВЛЯЮ КОЛИЧЕСТВО ПРЕДЛОЖЕНИЙ КАК В ОРИГИНАЛЬНОМ ТЕКСТЕ
                • работает только с частью 4
                 """),
            verbose=True
        )
    
    def final_editor_agent(self):
        return Agent(
            role="главный редактор для dzen.ru",
            goal='финальная редакция всего поста для dzen.ru',
            backstory=dedent("""\
                Я главный редактор контента для dzen.ru.

                Ваши задачи:
                • сделать финальную редакцию всего текста
                • проверить связность между частями
                • убедиться что текст соответствует формату dzen.ru
                • сохранить структуру с разделением на 4 части
                 """),
            verbose=True
        )