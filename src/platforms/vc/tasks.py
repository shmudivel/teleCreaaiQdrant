from textwrap import dedent
from crewai import Task

class VCTasks:
    """Tasks for creating vc.ru content."""
    
    def content_creation_task(self, agent, structure_part):
        return Task(
            description=dedent(f"""\
                1 part of 4 parts of content
                {structure_part}"""),
            expected_output=dedent("""\
                Готовый пост для vc.ru:
                - сделать тон более разговорным и дружелюбным
                - редактировать только --- part 1 --- остальное не трогать
                - создать яркий заголовок, который вызовет желание читать дальше
                - первые 2-3 предложения должны сразу вовлекать читателя
                - добавлять эмодзи для эмоциональности и лучшего восприятия
                - использовать простой и понятный язык
                - включить элементы сторителлинга для удержания внимания"""),
            agent=agent
        )
    
    def content_creation_task_part2(self, agent, structure_part):
        return Task(
            description=dedent(f"""\
                2 part of 4 parts of content
                {structure_part}"""),
            expected_output=dedent("""\
                Готовый пост для vc.ru:
                - сделать тон более разговорным и дружелюбным
                - редактировать только --- part 2 --- остальное не трогать
                - использовать короткие абзацы и простые предложения
                - добавлять эмодзи для структурирования и акцентов
                - включить примеры из жизни или ситуации, близкие аудитории
                - поддерживать стиль и тон первой части
                - использовать разговорные обороты, делающие текст более живым"""),
            agent=agent
        )
    
    def content_creation_task_part3(self, agent, structure_part):
        return Task(
            description=dedent(f"""\
                3 part of 4 parts of content
                {structure_part}"""),
            expected_output=dedent("""\
                Готовый пост для vc.ru:
                - сделать тон более разговорным и дружелюбным
                - редактировать только --- part 3 --- остальное не трогать
                - продолжать поддерживать интерес читателя
                - добавить интерактивные элементы (риторические вопросы)
                - использовать эмодзи и разделители для лучшей читаемости
                - поддерживать стиль и тон предыдущих частей
                - добавить личный опыт или мнение для большей аутентичности"""),
            agent=agent
        )
    
    def content_creation_task_part4(self, agent, structure_part):
        return Task(
            description=dedent(f"""\
                4 part of 4 parts of content
                {structure_part}"""),
            expected_output=dedent("""\
                Готовый пост для vc.ru:
                - сделать тон более разговорным и дружелюбным
                - редактировать только --- part 4 --- остальное не трогать
                - создать мощное завершение, которое вдохновит читателя
                - добавить призывы к действию (поделиться мнением, лайкнуть, сохранить)
                - задать вопрос для обсуждения в комментариях
                - использовать эмодзи для эмоциональности
                - сделать финальный акцент на главной мысли поста"""),
            agent=agent
        )
    
    def seo_optimization_task(self, agent, combined_content):
        return Task(
            description=dedent(f"""\
                SMM-оптимизация готового поста:
                
                {combined_content}"""),
            expected_output=dedent("""\
                Оптимизированный пост для vc.ru:
                - добавить 3-5 релевантных хештегов
                - оптимизировать под алгоритмы vc.ru
                - добавить элементы для повышения вовлеченности
                - включить trending topics, если уместно
                - проверить эмоциональную окраску текста
                - добавить интерактивные элементы для вовлечения аудитории"""),
            agent=agent
        )
    
    def final_editing_task(self, agent, combined_content):
        return Task(
            description=dedent(f"""\
                Финальная редакция готового поста из 4 частей для vc.ru:
                
                {combined_content}"""),
            expected_output=dedent("""\
                Готовый пост для vc.ru:
                - проверить связность между всеми четырьмя частями
                - обеспечить единый стиль и тон через весь пост
                - финализировать хештеги и интерактивные элементы
                - сделать пост ярким, вовлекающим и вирусным"""),
            agent=agent
        ) 