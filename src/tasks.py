from textwrap import dedent
from crewai import Task

class SocialMediaTask():
    def content_creation_task(self, agent, source_content):
        return Task(
            description=dedent(f"""\
                Создать адаптированный контент для социальных сетей на основе:
                {source_content}"""),
            expected_output=dedent("""\
                Готовый пост с:
                - Сохранением основной идеи
                - Оптимальным форматом для платформы
                - Призывом к действию"""),
            agent=agent
        )