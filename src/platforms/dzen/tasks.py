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
                - писать от первого лица, как будто я сам пишу статью
                - прописать и доказать авторитетность меня автора Сергея черненко
                - это не видео а статья, не используету "А еще в конце видео я поделюсь" подобные фразу 
                - приветствия быть не должно, так как это статья
                - придерживаться причинно-следственной связи между обзацами
                - стиль/тон бизнес деловой 
                - для каждого абзаца заголовок не нужен 
                - пост от первого лица"""),
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
                - релевантные данные из базы знаний через tools
                - добавлять драммотичность и эмоциональность где уместно
                - придерживаться причинно-следственной связи между обзацами
                - стиль/тон бизнес деловой
                - для каждого абзаца заголовок не нужен"""),
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
                -  добавть еще релевантные данные из базы знаний через tools
                - придерживаться причинно-следственной связи между обзацами
                - стиль/тон бизнес деловой
                - для каждого абзаца заголовок не нужен"""),
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
                - добавть еще релевантные данные из базы знаний через tools
                - сделать сильное завершение статьи
                - придерживаться причинно-следственной связи между обзацами
                - стиль/тон бизнес деловой
                - для каждого абзаца заголовок не нужен"""),
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
                - причинно-следственная связь между частями"""),
            agent=agent
        )

    def literary_editing_task(self, agent, content):

        return Task(
            description=f"""
            Review and enhance the literary quality of the following content:
            
            {content}
            
            Your task is to:
            1. Improve the flow and readability of the text

            """,
            agent=agent,
            expected_output="The content with improved literary style and readability"
        )
