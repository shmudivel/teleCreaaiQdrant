from textwrap import dedent
from crewai import Agent
from src.vector_db_tool import VectorDBToolset
import json

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
        
    def __init__(self, insights_processor=None):
        """
        Initialize Dzen agents with optional content insights processor.
        
        Args:
            insights_processor: ContentInsightsProcessor instance for structured insights
        """
        self.insights_processor = insights_processor

    def content_creator_agent(self):
        vdb_tools = VectorDBToolset()
        
        # Get part-specific insights if available
        insights_str = ""
        if self.insights_processor:
            insights = self.insights_processor.get_part_enhancement(1)
            if not insights.get("error"):
                insights_str = self._format_part_insights(insights, 1)
        
        return Agent(
            role="редактор контента для dzen.ru",
            goal='редактировать только часть 1 из 4 частей контента',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для dzen.ru.
                
                для контекста: {self.TARGET_AUDIENCE}
                
                {insights_str}

                Ваши задачи:
                • редактирует и четко придерживаться задания"""),
            verbose=True
        )
    
    def content_creator_agent_part2(self):
        vdb_tools = VectorDBToolset()
        
        # Get part-specific insights if available
        insights_str = ""
        if self.insights_processor:
            insights = self.insights_processor.get_part_enhancement(2)
            if not insights.get("error"):
                insights_str = self._format_part_insights(insights, 2)
        
        return Agent(
            role="редактор контента для dzen.ru",
            goal='редактировать только часть 2 из 4 частей контента',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для dzen.ru.
                
                для контекста: {self.TARGET_AUDIENCE}
                
                {insights_str}
                             
                Ваши задачи:
                • редактирует и четко придерживаться задания
                • работает только с частью 2 """),
            verbose=True
        )
    
    def content_creator_agent_part3(self):
        vdb_tools = VectorDBToolset()
        
        # Get part-specific insights if available
        insights_str = ""
        if self.insights_processor:
            insights = self.insights_processor.get_part_enhancement(3)
            if not insights.get("error"):
                insights_str = self._format_part_insights(insights, 3)
        
        return Agent(
            role="редактор контента для dzen.ru",
            goal='редактировать только часть 3 из 4 частей контента',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для dzen.ru.
                
                для контекста: {self.TARGET_AUDIENCE}
                
                {insights_str}
                             
                Ваши задачи:
                • редактирует и четко придерживаться задания
                • работает только с частью 3
                 """),
            verbose=True
        )
    
    def content_creator_agent_part4(self):
        vdb_tools = VectorDBToolset()
        
        # Get part-specific insights if available
        insights_str = ""
        if self.insights_processor:
            insights = self.insights_processor.get_part_enhancement(4)
            if not insights.get("error"):
                insights_str = self._format_part_insights(insights, 4)
        
        return Agent(
            role="редактор контента для dzen.ru",
            goal='редактировать только часть 4 из 4 частей контента',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для dzen.ru.
                
                для контекста: {self.TARGET_AUDIENCE}
                
                {insights_str}
                             
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
        # Get final editing insights if available
        insights_str = ""
        if self.insights_processor:
            final_insights = self.insights_processor.get_final_editing_data()
            insights_str = self._format_final_insights(final_insights)
        
        return Agent(
            role="главный редактор для dzen.ru",
            goal='финальная редакция всего поста для dzen.ru',
            backstory=dedent(f"""\
                Я главный редактор контента для dzen.ru.

                для контекста: {self.TARGET_AUDIENCE}
                
                {insights_str}

                Ваши задачи:
                • сделать финальную редакцию всего текста
                • проверить связность между частями
                • убедиться что текст соответствует формату dzen.ru
                • сохранить структуру с разделением на 4 части
                 """),
            verbose=True
        )

    def _format_part_insights(self, insights, part_num):
        """Format part insights for agent backstory."""
        formatted = dedent(f"""\
            СТРУКТУРИРОВАННЫЕ ИНСАЙТЫ ДЛЯ ЧАСТИ {part_num} (используйте их для улучшения качества контента):
            
            ТОН ТЕКСТА: {insights.get('tone', 'Не указан')}
            
            КЛЮЧЕВАЯ СУТЬ: {insights.get('key_essence', 'Не указана')}
            """)
            
        # Add facts if available
        facts = insights.get('key_facts', [])
        if facts:
            formatted += "КЛЮЧЕВЫЕ ФАКТЫ И ЦИФРЫ:\n"
            for i, fact in enumerate(facts, 1):
                formatted += f"  {i}. {fact}\n"
            formatted += "\n"
            
        # Add personal stories if available
        stories = insights.get('personal_stories', [])
        if stories:
            formatted += "ОПЫТ И ИСТОРИИ СЕРГЕЯ ЧЕРНЕНКО:\n"
            for i, story in enumerate(stories, 1):
                formatted += f"  {i}. {story}\n"
            formatted += "\n"
            
        # Add headline options for part 1
        if part_num == 1:
            headline_options = insights.get('headline_options', [])
            if headline_options:
                formatted += "ВАРИАНТЫ ЗАГОЛОВКОВ (для привлечения внимания):\n"
                for i, option in enumerate(headline_options, 1):
                    formatted += f"  {i}. {option}\n"
                formatted += "\n"
                
        # Add emotional hooks
        emotional_hooks = insights.get('emotional_hooks', [])
        if emotional_hooks:
            formatted += "ЭМОЦИОНАЛЬНЫЕ ЗАЦЕПКИ (для вовлечения читателя):\n"
            for i, hook in enumerate(emotional_hooks, 1):
                formatted += f"  {i}. {hook}\n"
            formatted += "\n"
            
        # Add expertise highlights if relevant
        if part_num in [1, 4]:
            expertise = insights.get('expertise_highlights', [])
            if expertise:
                formatted += "ЭКСПЕРТНЫЕ ЗНАНИЯ ДЛЯ ПОДЧЕРКИВАНИЯ:\n"
                for i, exp in enumerate(expertise, 1):
                    formatted += f"  {i}. {exp}\n"
                formatted += "\n"
                
        return formatted
        
    def _format_final_insights(self, insights):
        """Format final insights for final editor agent."""
        formatted = dedent("""\
            СТРУКТУРИРОВАННЫЕ ИНСАЙТЫ ДЛЯ ФИНАЛЬНОЙ РЕДАКЦИИ:
            
            КЛЮЧЕВЫЕ СУТИ ЧАСТЕЙ (используйте для обеспечения связности):
            """)
            
        # Add part essences
        part_essences = insights.get('part_essences', [])
        for i, essence in enumerate(part_essences, 1):
            if essence:
                formatted += f"  Часть {i}: {essence}\n"
                
        # Add discussion topics
        discussion_topics = insights.get('discussion_topics', [])
        if discussion_topics:
            formatted += "\nПОТЕНЦИАЛЬНЫЕ ТЕМЫ ДЛЯ ДИСКУССИИ (используйте для создания интригующего закрытия):\n"
            for i, topic in enumerate(discussion_topics, 1):
                formatted += f"  {i}. {topic}\n"
                
        # Add headline triggers
        headline_triggers = insights.get('all_headline_triggers', [])
        if headline_triggers:
            formatted += "\nКЛЮЧЕВЫЕ ТРИГГЕРЫ ДЛЯ ЗАГОЛОВКОВ (убедитесь, что финальная версия их использует):\n"
            for i, trigger in enumerate(headline_triggers, 1):
                formatted += f"  {i}. {trigger}\n"
                
        # Add expertise
        expertise = insights.get('expertise', [])
        if expertise:
            formatted += "\nЭКСПЕРТНЫЕ ЗНАНИЯ АВТОРА (убедитесь, что они достаточно отражены в тексте):\n"
            for i, exp in enumerate(expertise, 1):
                formatted += f"  {i}. {exp}\n"
                
        return formatted

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