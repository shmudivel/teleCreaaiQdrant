from textwrap import dedent
from crewai import Agent
from src.vector_db_tool import VectorDBToolset

class DzenAgents:
    """Agents for creating Dzen.ru content."""
    
    TARGET_AUDIENCE = dedent("""\
        Целевая аудитория:
        Сотрудники 25-45 лет, работающие в найме 3-5+ лет на одной позиции.
        Хотят повышения зарплаты/должности, но:
        - Не понимают корпоративных процессов продвижения
        - Боятся менять работу из-за кредитов/неуверенности
        - Тратят силы на дополнительную работу вместо стратегического развития
        - Не умеют выстраивать отношения с руководством и HR
        - Нуждаются в практических советах по карьерному позиционированию
        ТЕЗИС - не уходите в свой бизнес, продолжайте работать в найме""")

    def content_creator_agent(self):
        vdb_tools = VectorDBToolset()
        return Agent(
            role="редактор контента для dzen.ru",
            goal='редактировать только часть 1 из 4 частей контента',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для dzen.ru.
                
                для контекста: {self.TARGET_AUDIENCE}

                Ваши задачи:
                • редактирует и четко придерживаться задания"""),
            verbose=True
        )
    
    def content_creator_agent_part2(self):
        vdb_tools = VectorDBToolset()
        return Agent(
            role="редактор контента для dzen.ru",
            goal='редактировать только часть 2 из 4 частей контента',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для dzen.ru.
                
                для контекста: {self.TARGET_AUDIENCE}
                             
                Ваши задачи:
                • редактирует и четко придерживаться задания
                • работает только с частью 2 """),
            verbose=True
        )
    
    def content_creator_agent_part3(self):
        vdb_tools = VectorDBToolset()
        return Agent(
            role="редактор контента для dzen.ru",
            goal='редактировать только часть 3 из 4 частей контента',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для dzen.ru.
                
                для контекста: {self.TARGET_AUDIENCE}
                             
                Ваши задачи:
                • редактирует и четко придерживаться задания
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
            backstory=dedent(f"""\
                Я профессиональный редактор контента для dzen.ru.
                
                для контекста: {self.TARGET_AUDIENCE}
                             
                Ваши задачи:
                • редактирует и четко придерживаться задания
                • работает только с частью 4
                 """),
            verbose=True
        )

    # def seo_optimizer_agent(self):
    #     return Agent(
    #         role="SEO специалист для Dzen.ru",
    #         goal='оптимизировать текст для поисковых систем',
    #         backstory=dedent("""\
    #             Я профессиональный SEO-оптимизатор контента для dzen.ru.

    #             Ваши задачи:
    #             • анализировать семантическое ядро
    #             • добавлять ключевые слова естественным образом
    #             • оптимизировать плотность ключей (2-3%)
    #             • создавать мета-описания
    #             • добавлять LSI-слова
    #             • проверять внутреннюю перелинковку
    #             """),
    #         verbose=True
    #     )
    


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

    # def literary_editor_agent(self):
    #     """
    #     Creates a literary editor agent that improves the writing style and readability.
    #     """
    #     return Agent(
    #         role="Literary Editor",
    #         goal="Enhance the literary quality and readability of the content",
    #         backstory="""fix typos and grammar errors, improve the flow and readability of the text""",
    #         verbose=True,
    #         allow_delegation=False,
    #         tools=[],
    #     ) 