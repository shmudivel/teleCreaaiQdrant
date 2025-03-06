from textwrap import dedent
from crewai import Task

class DzenTasks:
    """Tasks for creating Dzen.ru content."""
    
    def content_creation_task(self, agent, structure_part):
        return Task(
            description=dedent(f"""\
                1 part of 4 parts of content
                {structure_part}"""),
            expected_output=dedent("""\
                Готовый пост для dzen.ru:
                - редактировать только --- part 1 --- остальное не трогать
                - можно добавть еще релевантные данные из базы знаний через tools
                - ВАЖНО! создать цепляющий H1 заголовок (6-8 слов) - это 50% успеха статьи
                - ВАЖНО! первые 2-3 предложения должны захватывать внимание и раскрывать суть иначе не будет читателей
                - это не видео а статья, не используету "А еще в конце видео я поделюсь" подобные фразу 
                - приветствия быть не должно, так как это статья"""),
            agent=agent
        )
    
    def content_creation_task_part2(self, agent, structure_part):
        return Task(
            description=dedent(f"""\
                2 part of 4 parts of content
                {structure_part}"""),
            expected_output=dedent("""\
                Готовый пост для dzen.ru:
                - редактировать только --- part 2 --- остальное не трогать
                - добавить еще релевантные данные из базы знаний через tools
                - добавлять драммотичность и эмоциональность где уместно"""),
            agent=agent
        )
    
    def content_creation_task_part3(self, agent, structure_part):
        return Task(
            description=dedent(f"""\
                3 part of 4 parts of content
                {structure_part}"""),
            expected_output=dedent("""\
                Готовый пост для dzen.ru:
                - редактировать только --- part 3 --- остальное не трогать
                - можно добавть еще релевантные данные из базы знаний через tools"""),
            agent=agent
        )
    
    def content_creation_task_part4(self, agent, structure_part):
        return Task(
            description=dedent(f"""\
                4 part of 4 parts of content
                {structure_part}"""),
            expected_output=dedent("""\
                Готовый пост для dzen.ru:
                - редактировать только --- part 4 --- остальное не трогать
                - можно добавть еще релевантные данные из базы знаний через tools
                - сделать сильное завершение статьи"""),
            agent=agent
        )
    
    def seo_optimization_task(self, agent, combined_content):
        return Task(
            description=dedent(f"""\
                SEO оптимизация готового поста:
                
                {combined_content}"""),
            expected_output=dedent("""\
                Оптимизированный пост для dzen.ru:
                - SEO: добавить 3-5 основных ключевых слов
                - SEO: использовать LSI-слова (минимум 5)
                - SEO: оптимизировать заголовки H2-H3
                - SEO: создать мета-описание с главным ключом
                - SEO: проверить плотность ключей (2-3%)
                - SEO: отчет оптимезаций в конце статьи большими буквами"""),
            agent=agent
        )
    
    
    def final_editing_task(self, agent, combined_content):
        return Task(
            description=dedent(f"""\
                Финальная редакция готового поста из 4 частей для dzen.ru:
                
                {combined_content}"""),
            expected_output=dedent("""\
                Готовый пост для dzen.ru:
                - проверить связность между всеми четырьмя частями
                - исправить стилистические ошибки
                - причинно-следственная связь между частями"""),
            agent=agent
        )

    def literary_editing_task(self, agent, content):
        """
        Creates a task for literary editing of the content.
        
        Args:
            agent: The literary editor agent
            content: The content to be edited
        
        Returns:
            Task: A task for literary editing
        """
        return Task(
            description=f"""
            Review and enhance the literary quality of the following content:
            
            {content}
            
            Your task is to:
            1. Improve the flow and readability of the text
            2. Enhance vocabulary and word choice where appropriate
            3. Fix awkward phrasing and sentence structures
            4. Ensure a consistent and engaging voice throughout
            5. Make the content more captivating while preserving all information
            6. Maintain the original structure with the part divisions
            
            Return the improved version of the content with enhanced literary quality.
            """,
            agent=agent,
            expected_output="The content with improved literary style and readability, maintaining the original structure with part divisions."
        )
