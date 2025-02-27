from textwrap import dedent
from crewai import Task

class SocialMediaTask():
    def content_creation_task(self, agent, source_content):
        return Task(
            description=dedent(f"""\
                1 part of 4 parts of content
                {source_content}"""),
            expected_output=dedent("""\
                Готовый пост для dzen.ru:
                - редактировать только --- part 1 --- остальное не трогать
                - можно добавть еще релевантные данные из базы знаний через tools
                - и написать нужно по всем правилам для dzen.ru
                - и по лучшим рактиками продающего поста
                - приветствия быть не должно, так как это статья"""),
            agent=agent
        )
    
    def content_creation_task_part2(self, agent, source_content):
        return Task(
            description=dedent(f"""\
                2 part of 4 parts of content
                {source_content}"""),
            expected_output=dedent("""\
                Готовый пост для dzen.ru:
                - редактировать только --- part 2 --- остальное не трогать
                - можно добавть еще релевантные данные из базы знаний через tools
                - и написать нужно по всем правилам для dzen.ru
                - и по лучшим рактиками продающего поста
                - соблюдать стиль и тон первой части"""),
            agent=agent
        )
    
    def content_creation_task_part3(self, agent, source_content):
        return Task(
            description=dedent(f"""\
                3 part of 4 parts of content
                {source_content}"""),
            expected_output=dedent("""\
                Готовый пост для dzen.ru:
                - редактировать только --- part 3 --- остальное не трогать
                - можно добавть еще релевантные данные из базы знаний через tools
                - и написать нужно по всем правилам для dzen.ru
                - и по лучшим рактиками продающего поста
                - соблюдать стиль и тон предыдущих частей"""),
            agent=agent
        )
    
    def content_creation_task_part4(self, agent, source_content):
        return Task(
            description=dedent(f"""\
                4 part of 4 parts of content
                {source_content}"""),
            expected_output=dedent("""\
                Готовый пост для dzen.ru:
                - редактировать только --- part 4 --- остальное не трогать
                - можно добавть еще релевантные данные из базы знаний через tools
                - и написать нужно по всем правилам для dzen.ru
                - и по лучшим рактиками продающего поста
                - сделать сильное завершение статьи
                - соблюдать стиль и тон предыдущих частей"""),
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
                - улучшить заголовки и подзаголовки
                - убедиться в соответствии формату dzen.ru
                - СОХРАНИТЬ СТРУКТУРУ с разделением на 4 части
                - СОХРАНИТЬ ВСЕ МАРКЕРЫ ЧАСТЕЙ (--- Part X ---)"""),
            agent=agent
        )