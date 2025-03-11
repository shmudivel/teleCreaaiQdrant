from textwrap import dedent
from crewai import Agent
from src.vector_db_tool import VectorDBToolset
import json
from src.text_analyzer import extract_insights

class VCAgents:
    """Agents for creating VC.ru content."""
    
    TARGET_AUDIENCE = dedent("""\
        Целевая аудитория:
        Предприниматели и специалисты 25-45 лет, интересующиеся бизнесом и технологиями.
        Характеристики:
        - Активно следят за трендами в бизнесе и технологиях
        - Ищут практические советы и кейсы для применения
        - Ценят экспертное мнение и реальный опыт
        - Интересуются стартапами и инновациями
        - Готовы к дискуссиям и обмену опытом
        ТЕЗИС - делиться реальным опытом, успехами и неудачами""")
        
    ACCURACY_GUIDELINES = dedent("""\
        ПРАВИЛА ТОЧНОСТИ:
        1. ВСЕГДА использовать настоящее имя автора - Сергей Черненко (не заменять на "[Имя автора]")
        2. Каждый термин и концепция должны быть взяты из оригинального текста - НЕ ИЗОБРЕТАТЬ новые
        3. Сохранять оригинальную терминологию (например, использовать "дело" вместо "бизнес", если так в оригинале)
        4. Все цифры, статистика и финансовые данные должны быть ТОЧНО как в оригинале
        5. Все личные истории и примеры автора должны передаваться без искажений
        6. Все профессиональные термины должны быть объяснены при первом упоминании
        7. Избегать неоднозначных или запутанных формулировок
        8. Не использовать академический или чрезмерно формальный язык""")
    
    STRUCTURE_GUIDELINES = dedent("""\
        ПРАВИЛА СТРУКТУРЫ:
        1. Создавать полноценные абзацы из 3-5 связанных по смыслу предложений
        2. НЕ ИСПОЛЬЗОВАТЬ одиночные слова или короткие фразы как отдельные предложения
        3. Избегать абзацев из одного предложения
        4. Обеспечивать плавные переходы между предложениями и абзацами
        5. Сохранять логическую последовательность в развитии мыслей
        6. Использовать естественный деловой стиль речи без странных оборотов
        7. Сохранять синтаксическую структуру, характерную для автора
        8. Использовать авторские риторические приемы (метафоры, примеры, сравнения)""")
    
    def __init__(self, insights_processor=None):
        """
        Initialize VC agents with optional content insights processor.
        
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
            role="редактор контента для vc.ru",
            goal='создать первую часть статьи, сохраняя оригинальный стиль и тон автора',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для vc.ru с глубоким пониманием авторского стиля.
                
                Целевая аудитория: {self.TARGET_AUDIENCE}
                
                {style_guide}
                
                {self.ACCURACY_GUIDELINES}
                
                {self.STRUCTURE_GUIDELINES}
                
                {part_insights}

                Мои задачи:
                • Сохранить авторский голос и стиль письма исходного текста
                • Создать захватывающее начало, при этом оставаясь верным исходному тону
                • Использовать имя автора (Сергей Черненко) где это уместно
                • Обеспечить плавные переходы между абзацами и логическую структуру
                • Использовать фактические данные и истории из оригинала, не добавляя выдуманных деталей
                • Создать контент, который будет привлекательным для аудитории VC.ru"""),
            verbose=True
        )
    
    def content_creator_agent_part2(self):
        vdb_tools = VectorDBToolset()
        
        # Get part-specific insights and general text style
        part_insights = self._get_enhanced_part_insights(2)
        style_guide = self._get_style_guide()
        
        return Agent(
            role="редактор контента для vc.ru",
            goal='создать вторую часть статьи, сохраняя стилистическую связность с первой частью',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для vc.ru с глубоким пониманием авторского стиля.
                
                Целевая аудитория: {self.TARGET_AUDIENCE}
                
                {style_guide}
                
                {self.ACCURACY_GUIDELINES}
                
                {self.STRUCTURE_GUIDELINES}
                
                {part_insights}
                             
                Мои задачи:
                • Продолжить повествование в том же стиле и тоне, что и первая часть
                • Сохранить авторский голос и индивидуальные особенности речи
                • Обеспечить плавный переход от первой части ко второй
                • Развить аргументацию и углубить основные идеи
                • Использовать имя автора (Сергей Черненко) где это уместно
                • Сохранить логическую структуру и причинно-следственные связи оригинала"""),
            verbose=True
        )
    
    def content_creator_agent_part3(self):
        vdb_tools = VectorDBToolset()
        
        # Get part-specific insights and general text style
        part_insights = self._get_enhanced_part_insights(3)
        style_guide = self._get_style_guide()
        
        return Agent(
            role="редактор контента для vc.ru",
            goal='создать третью часть статьи с сохранением тона и углублением основных идей',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для vc.ru с глубоким пониманием авторского стиля.
                
                Целевая аудитория: {self.TARGET_AUDIENCE}
                
                {style_guide}
                
                {self.ACCURACY_GUIDELINES}
                
                {self.STRUCTURE_GUIDELINES}
                
                {part_insights}
                
                Мои задачи:
                • Сохранить целостность повествования и связь с предыдущими частями
                • Углубить основные идеи, используя тот же авторский стиль
                • Использовать имя автора (Сергей Черненко) где это уместно
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
            role="редактор контента для vc.ru",
            goal='создать завершающую часть статьи с логичным заключением в стиле автора',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я профессиональный редактор контента для vc.ru с глубоким пониманием авторского стиля.
                
                Целевая аудитория: {self.TARGET_AUDIENCE}
                
                {style_guide}
                
                {self.ACCURACY_GUIDELINES}
                
                {self.STRUCTURE_GUIDELINES}
                
                {part_insights}
                
                Мои задачи:
                • Создать мощное заключение в тоне и стиле автора
                • Сохранить целостность повествования и связь с предыдущими частями
                • Подвести итоги, следуя логике авторской аргументации
                • Использовать имя автора (Сергей Черненко) где это уместно
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
            role="главный редактор для vc.ru",
            goal='обеспечить стилистическое и смысловое единство всего текста',
            tools=vdb_tools.tools(),
            backstory=dedent(f"""\
                Я главный редактор контента для vc.ru с экспертизой в создании целостных, стилистически единых текстов.
                
                Целевая аудитория: {self.TARGET_AUDIENCE}
                
                {style_guide}
                
                {self.ACCURACY_GUIDELINES}
                
                {self.STRUCTURE_GUIDELINES}
                
                {final_insights}
                
                Мои задачи:
                • Обеспечить полную связность всех четырех частей текста
                • Устранить стилистические несоответствия между частями
                • Проверить логику причинно-следственных связей по всему тексту
                • Проверить правильное использование имени автора (Сергей Черненко)
                • Исправить любые одиночные слова, используемые как предложения
                • Устранить короткие, отрывистые абзацы из 1-2 предложений
                • Проверить точность всех цифр и статистических данных
                • Сохранить целостный авторский голос и единство тона
                • Убедиться, что текст читается как единое произведение, а не набор разрозненных частей
                • Финализировать текст для публикации на VC.ru, обеспечивая его привлекательность для целевой аудитории"""),
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
                if key != "error":
                    formatted += f"- {key}: {value}\n"
        elif isinstance(insights, str):
            formatted += insights
            
        return formatted
    
    def _get_final_editing_insights(self):
        """Get insights for final editing from holistic analysis."""
        if not self.holistic_analysis:
            return ""
            
        try:
            # Create a formatted insight for final editing
            overall_style = self.holistic_analysis.get('overall_style', 'Не определен')
            coherence = self.holistic_analysis.get('coherence', 'Не определена')
            emotional_triggers = ', '.join(self.holistic_analysis.get('emotional_triggers', ['Не определены']))
            author_uniqueness = ', '.join(self.holistic_analysis.get('author_uniqueness', ['Не определены']))
            
            final_insights = f"""
            ЦЕЛОСТНЫЙ АНАЛИЗ ТЕКСТА:
            
            - Общий стиль: {overall_style}
            - Связность между частями: {coherence}
            - Эмоциональные триггеры: {emotional_triggers}
            - Уникальные авторские особенности: {author_uniqueness}
            """
            
            # Add VC potential if available
            vc_potential = extract_insights(self.insights_processor.get_full_analysis(), 'vc_potential')
            if vc_potential:
                hooks = ', '.join(vc_potential.get('attention_hooks', ['Не определены']))
                emotional_points = ', '.join(vc_potential.get('emotional_points', ['Не определены']))
                discussion_topics = ', '.join(vc_potential.get('discussion_topics', ['Не определены']))
                audience_relevance = vc_potential.get('audience_relevance', 'Не определена')
                
                final_insights += f"""
                ПОТЕНЦИАЛ ДЛЯ VC.RU:
                
                - Крючки внимания: {hooks}
                - Эмоциональные точки: {emotional_points}
                - Темы для дискуссии: {discussion_topics}
                - Соответствие целевой аудитории: {audience_relevance}
                """
                
            return final_insights
            
        except Exception:
            # Fall back to simpler formatting
            return self._format_final_insights(self.holistic_analysis)
    
    def _format_final_insights(self, insights):
        """Format final insights in a readable way (backward compatibility)."""
        formatted = "ЦЕЛОСТНЫЙ АНАЛИЗ ТЕКСТА:\n\n"
        
        if isinstance(insights, dict):
            for key, value in insights.items():
                if isinstance(value, list):
                    value = ', '.join(value)
                formatted += f"- {key}: {value}\n"
        elif isinstance(insights, str):
            formatted += insights
            
        return formatted
    
    def _get_style_guide(self):
        """Get a style guide based on analysis or default guidelines."""
        if not self.holistic_analysis:
            return dedent("""\
                СТИЛИСТИЧЕСКОЕ РУКОВОДСТВО:
                
                • Использовать деловой, но доступный стиль письма
                • Сохранять авторский голос и индивидуальные особенности речи
                • Избегать академичности и сухости изложения
                • Адаптировать контент под целевую аудиторию, но сохранить суть и тон автора
                • Использовать подходящие риторические приемы для удержания внимания
                • Обеспечить четкую структуру и логические переходы между частями
                • Следовать естественному языку автора, избегая искусственных конструкций
                • Сохранять точность и достоверность всех фактов и данных
                • Убедиться, что каждая часть имеет законченный смысл и встраивается в общую картину
                • Сохранять авторское отношение к описываемым явлениям и ситуациям""")
                
        try:
            # Create a style guide based on holistic analysis
            overall_style = self.holistic_analysis.get('overall_style', '')
            author_uniqueness = self.holistic_analysis.get('author_uniqueness', [])
            
            if not overall_style or not author_uniqueness:
                return self._get_style_guide()
                
            uniqueness_points = '\n• '.join(author_uniqueness)
            
            return dedent(f"""\
                СТИЛИСТИЧЕСКОЕ РУКОВОДСТВО (на основе анализа):
                
                ОБЩИЙ СТИЛЬ:
                {overall_style}
                
                УНИКАЛЬНЫЕ ОСОБЕННОСТИ АВТОРА:
                • {uniqueness_points}
                
                РЕКОМЕНДАЦИИ:
                • Сохранять уникальный авторский голос на протяжении всего текста
                • Воспроизводить синтаксические и лексические особенности
                • Использовать те же риторические приемы и эмоциональные триггеры
                • Адаптировать контент, сохраняя авторскую индивидуальность
                • Обеспечить точность в передаче фактов и данных
                • Сохранять логику причинно-следственных связей оригинала""")
                
        except Exception:
            # Fall back to default style guide
            return self._get_style_guide() 