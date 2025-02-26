from textwrap import dedent
from crewai import Task


class contentSocialMediaTasks():
    def content_analysis_task(self, agent, youtube_content):
        return Task(
            description=dedent(f"""\
                анализ текста добавляем релевантные данные из базы знаний
                {youtube_content}"""),
            expected_output=dedent("""\
                не меняя ориентацию на контент, добавляем релевантные данные из базы знаний"""),
            agent=agent
        )
    
    def create_dzen_post_task(self, agent, content_analysis, youtube_content):
        return Task(
            description=dedent(f"""\
                пишем пост для дзен на основе контента 
                но при это сохраняем длинну контента как в исходном тексте 
                {youtube_content}

                Анализ контента:
                {content_analysis}"""),
            expected_output=dedent("""\
                Готовый пост для Дзен с:
                - сохранением длинны контента
                - добавлением релевантных данных из базы знаний,
                - Призывом к действию"""),
            agent=agent
        )
    
    def create_vc_post_task(self, agent, content_analysis, youtube_content):
        return Task(
            description=dedent(f"""\
                пишем пост для vc.ru на основе контента
                но при это сохраняем длинну контента как в исходном тексте 
                {youtube_content}

                Анализ контента:
                {content_analysis}"""),
            expected_output=dedent("""\
                Готовый пост для VC.ru с:
                - сохранением длинны контента
                - добавлением релевантных данных из базы знаний,
                - Бизнес-фокусом"""),
            agent=agent
        )