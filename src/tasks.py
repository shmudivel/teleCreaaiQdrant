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
                - можно добавть еще релевантные данные из базы знаний через tools"""),
            agent=agent
        )