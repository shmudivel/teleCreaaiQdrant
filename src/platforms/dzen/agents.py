from textwrap import dedent
from crewai import Agent
from src.vector_db_tool import VectorDBToolset
import json
from src.text_analyzer import extract_insights

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
        self.holistic_analysis = None
        
        # Extract holistic analysis if available
        if insights_processor:
            analysis_data = insights_processor.get_full_analysis()
            if analysis_data and not isinstance(analysis_data, str):
                try:
                    # Try to extract holistic analysis
                    self.holistic_analysis = extract_insights(analysis_data, 'holistic_analysis')
                except Exception:
                    self.holistic_analysis = None

    def content_creator_agent(self):
        vdb_tools = VectorDBToolset()
        
        # Get part-specific insights and general text style
        part_insights = self._get_enhanced_part_insights(1)
        style_guide = self._get_style_guide()
        
        return Agent(
            role="редактор контента для dzen.ru",
            goal='создать первую часть статьи, сохраняя оригинальный стиль и тон автора',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для dzen.ru с глубоким пониманием авторского стиля.
                
                Целевая аудитория: {self.TARGET_AUDIENCE}
                
                {style_guide}
                
                {part_insights}

                Мои задачи:
                • Сохранить авторский голос и стиль письма исходного текста
                • Создать захватывающее начало, при этом оставаясь верным исходному тону
                • Обеспечить плавные переходы между абзацами и логическую структуру
                • Использовать фактические данные и истории из оригинала, не добавляя выдуманных деталей
                • Создать контент, который будет привлекательным для аудитории Дзен"""),
            verbose=True
        )
    
    def content_creator_agent_part2(self):
        vdb_tools = VectorDBToolset()
        
        # Get part-specific insights and general text style
        part_insights = self._get_enhanced_part_insights(2)
        style_guide = self._get_style_guide()
        
        return Agent(
            role="редактор контента для dzen.ru",
            goal='создать вторую часть статьи, сохраняя стилистическую связность с первой частью',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для dzen.ru с глубоким пониманием авторского стиля.
                
                Целевая аудитория: {self.TARGET_AUDIENCE}
                
                {style_guide}
                
                {part_insights}
                             
                Мои задачи:
                • Продолжить повествование в том же стиле и тоне, что и первая часть
                • Сохранить авторский голос и индивидуальные особенности речи
                • Обеспечить плавный переход от первой части ко второй
                • Развить аргументацию и углубить основные идеи
                • Сохранить логическую структуру и причинно-следственные связи оригинала"""),
            verbose=True
        )
    
    def content_creator_agent_part3(self):
        vdb_tools = VectorDBToolset()
        
        # Get part-specific insights and general text style
        part_insights = self._get_enhanced_part_insights(3)
        style_guide = self._get_style_guide()
        
        return Agent(
            role="редактор контента для dzen.ru",
            goal='создать третью часть статьи с сохранением тона и углублением основных идей',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для dzen.ru с глубоким пониманием авторского стиля.
                
                Целевая аудитория: {self.TARGET_AUDIENCE}
                
                {style_guide}
                
                {part_insights}
                
                Мои задачи:
                • Сохранить целостность повествования и связь с предыдущими частями
                • Углубить основные идеи, используя тот же авторский стиль
                • Использовать такие же риторические приемы, как в оригинальном тексте
                • Конкретизировать аргументы данными и примерами из исходного материала
                • Поддерживать эмоциональный тон и лексические особенности автора"""),
            verbose=True
        )
    
    def content_creator_agent_part4(self):
        vdb_tools = VectorDBToolset()
        
        # Get part-specific insights and general text style
        part_insights = self._get_enhanced_part_insights(4)
        style_guide = self._get_style_guide()
        
        return Agent(
            role="редактор контента для dzen.ru",
            goal='создать завершающую часть статьи с логичным заключением в стиле автора',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для dzen.ru с глубоким пониманием авторского стиля.
                
                Целевая аудитория: {self.TARGET_AUDIENCE}
                
                {style_guide}
                
                {part_insights}
                
                Мои задачи:
                • Создать мощное заключение в тоне и стиле автора
                • Сохранить целостность повествования и связь с предыдущими частями
                • Подвести итоги, следуя логике авторской аргументации
                • Сформулировать призыв к действию, соответствующий авторскому посылу
                • Завершить текст так, чтобы он воспринимался как единое целое"""),
            verbose=True
        )
    
    def final_editor_agent(self):
        vdb_tools = VectorDBToolset()
        
        # Get holistic analysis for final editing
        final_insights = self._get_final_editing_insights()
        style_guide = self._get_style_guide()
        
        return Agent(
            role="главный редактор для dzen.ru",
            goal='обеспечить стилистическое и смысловое единство всего текста',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я главный редактор контента для dzen.ru с экспертизой в создании целостных, стилистически единых текстов.
                
                Целевая аудитория: {self.TARGET_AUDIENCE}
                
                {style_guide}
                
                {final_insights}
                
                Мои задачи:
                • Обеспечить полную связность всех четырех частей текста
                • Устранить стилистические несоответствия между частями
                • Проверить логику причинно-следственных связей по всему тексту
                • Сохранить целостный авторский голос и единство тона
                • Убедиться, что текст читается как единое произведение, а не набор разрозненных частей
                • Финализировать текст для публикации на Дзен, обеспечивая его привлекательность для целевой аудитории"""),
            verbose=True
        )
    
    def _get_enhanced_part_insights(self, part_num):
        """Get enhanced insights for a specific part with detailed tone and style guidance."""
        if not self.insights_processor:
            return ""
            
        insights = self.insights_processor.get_part_enhancement(part_num)
        if insights.get("error"):
            return ""
            
        try:
            # Get part analysis from full data
            analysis_data = self.insights_processor.get_full_analysis()
            parts_data = extract_insights(analysis_data)
            
            if not parts_data or not isinstance(parts_data, dict) or 'parts' not in parts_data:
                return self._format_part_insights(insights, part_num)
                
            # Find the correct part
            part_data = None
            for part in parts_data['parts']:
                if part.get('marker') == f"--- Part {part_num} ---":
                    part_data = part
                    break
                    
            if not part_data:
                return self._format_part_insights(insights, part_num)
                
            # Create enhanced insights with detailed tone and style guidance
            tone_analysis = part_data.get('tone_analysis', {})
            content_analysis = part_data.get('content_analysis', {})
            key_elements = part_data.get('key_elements', {})
            
            enhanced_insights = f"""
            АНАЛИЗ ЧАСТИ {part_num}:
            
            СТИЛЬ И ТОН АВТОРА:
            - Эмоциональный тон: {tone_analysis.get('emotional_tone', 'Не определен')}
            - Особенности лексики: {tone_analysis.get('lexical_features', 'Не определены')}
            - Синтаксические особенности: {tone_analysis.get('syntax_patterns', 'Не определены')}
            - Риторические приемы: {tone_analysis.get('rhetorical_devices', 'Не определены')}
            - Авторский голос: {tone_analysis.get('author_voice', 'Не определен')}
            
            КЛЮЧЕВЫЕ ЭЛЕМЕНТЫ:
            - Основные идеи: {', '.join(key_elements.get('main_ideas', ['Не определены']))}
            - Факты и цифры: {', '.join(key_elements.get('facts', ['Не определены']))}
            - Личные истории: {', '.join(key_elements.get('personal_stories', ['Не определены']))}
            - Уникальные инсайты: {', '.join(key_elements.get('unique_insights', ['Не определены']))}
            
            АНАЛИЗ СОДЕРЖАНИЯ:
            - Главная идея части: {content_analysis.get('main_idea', 'Не определена')}
            - Логический путь: {content_analysis.get('logic_path', 'Не определен')}
            - Основная суть: {content_analysis.get('key_essence', 'Не определена')}
            - Цель автора: {content_analysis.get('author_intention', 'Не определена')}
            """
            
            return enhanced_insights
            
        except Exception:
            # Fall back to basic formatting if enhanced parsing fails
            return self._format_part_insights(insights, part_num)
    
    def _format_part_insights(self, insights, part_num):
        """Format insights for a part in a readable way (backward compatibility)."""
        formatted = f"АНАЛИЗ ЧАСТИ {part_num}:\n\n"
        
        if isinstance(insights, dict):
            for key, value in insights.items():
                if key not in ["error", "part"]:
                    if isinstance(value, list):
                        formatted += f"{key.upper()}:\n"
                        for item in value:
                            formatted += f"- {item}\n"
                        formatted += "\n"
                    else:
                        formatted += f"{key.upper()}: {value}\n\n"
                        
        return formatted
    
    def _get_final_editing_insights(self):
        """Get insights for final editing with focus on holistic cohesion."""
        if not self.holistic_analysis:
            return ""
            
        try:
            holistic = self.holistic_analysis
            
            final_insights = f"""
            ЦЕЛОСТНЫЙ АНАЛИЗ ТЕКСТА:
            
            ОБЩИЙ СТИЛЬ И ТОН:
            {holistic.get('overall_style', 'Не определен')}
            
            СВЯЗНОСТЬ МЕЖДУ ЧАСТЯМИ:
            {holistic.get('coherence', 'Не определена')}
            
            ЭМОЦИОНАЛЬНЫЕ ТРИГГЕРЫ:
            {', '.join(holistic.get('emotional_triggers', ['Не определены']))}
            
            АВТОРСКИЕ ОСОБЕННОСТИ:
            {', '.join(holistic.get('author_uniqueness', ['Не определены']))}
            """
            
            return final_insights
            
        except Exception:
            # Fall back if holistic analysis isn't available
            return self._format_final_insights(self.insights_processor.get_final_enhancement() if self.insights_processor else {})
    
    def _format_final_insights(self, insights):
        """Format final insights in a readable way (backward compatibility)."""
        if not insights or insights.get("error"):
            return ""
            
        formatted = "ФИНАЛЬНЫЙ АНАЛИЗ:\n\n"
        
        if isinstance(insights, dict):
            for key, value in insights.items():
                if key != "error":
                    if isinstance(value, list):
                        formatted += f"{key.upper()}:\n"
                        for item in value:
                            formatted += f"- {item}\n"
                        formatted += "\n"
                    else:
                        formatted += f"{key.upper()}: {value}\n\n"
                        
        return formatted
        
    def _get_style_guide(self):
        """Generate a style guide based on holistic analysis or defaults."""
        if self.holistic_analysis:
            try:
                style = self.holistic_analysis.get('overall_style', 'Профессиональный деловой стиль с элементами разговорной речи')
                
                style_guide = f"""
                РУКОВОДСТВО ПО СТИЛЮ:
                
                ОБЩИЙ СТИЛЬ: {style}
                
                РЕКОМЕНДАЦИИ:
                • Сохраняйте авторский голос и манеру изложения
                • Используйте те же риторические приемы, что и в оригинале
                • Поддерживайте синтаксические особенности автора
                • Сохраняйте лексические характеристики исходного текста
                • Придерживайтесь эмоционального тона оригинала
                """
                
                return style_guide
                
            except Exception:
                pass
                
        # Default style guide if holistic analysis isn't available
        return """
        РУКОВОДСТВО ПО СТИЛЮ:
        
        ОБЩИЙ СТИЛЬ: Профессиональный деловой стиль с элементами разговорной речи
        
        РЕКОМЕНДАЦИИ:
        • Сохраняйте естественность и авторский голос текста
        • Используйте понятный, но профессиональный язык
        • Балансируйте между экспертностью и доступностью
        • Избегайте излишне формальных конструкций
        • Поддерживайте единый тон на протяжении всего текста
        """

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