from textwrap import dedent
from crewai import Task

class DzenTasks:
    """Tasks for creating Dzen.ru content."""
    
    def content_creation_task(self, agent, structure_part):
        return Task(
            description=dedent(f"""\
                Строго придерживаться полученной структуры текста для части 1/4:
                {structure_part}"""),
            expected_output=dedent(f"""\
                Полноценная первая часть статьи для dzen.ru:
                - Добавлять дополнительные данные из базы знаний через tools ТОЛЬКО если релевантны
                - Обязательные элементы:
                    * Заголовок в Дзене – 50% успеха
                  * Цепляющий H1 заголовок (6-8 слов) с главной benefit-темой части
                  * Первые 3 предложения: провокационный вопрос/утверждение + проблема аудитории
                - Формат:
                  * Без подзаголовков внутри части
                  * Плавные переходы между абзацами
                  * Деловой стиль с элементами разговорной речи
                  * От первого лица (я/мой опыт)
                  * Без видео-отсылок ("в этом видео") и приветствий"""),
            agent=agent
        )
    
    def content_creation_task_part2(self, agent, structure_part):
        return Task(
            description=dedent(f"""\
                Строго придерживаться полученной структуры текста для части 2/4:
                {structure_part}"""),
            expected_output=dedent(f"""\
                Полноценная вторая часть статьи для dzen.ru:
                - ТОЧНО сохранить структуру раздела part 2
                - Добавлять данные из базы знаний через tools ТОЛЬКО если релевантны
                - Обязательные элементы:
                  * Примеры из практического опыта
                  * Драматичность и эмоциональность где уместно
                - Формат:
                  * Плавные переходы между абзацами
                  * Причинно-следственная связь между блоками
                  * Деловой стиль с элементами разговорной речи
                  * Без подзаголовков внутри части"""),
            agent=agent
        )
    
    def content_creation_task_part3(self, agent, structure_part):
        return Task(
            description=dedent(f"""\
                Строго придерживаться полученной структуры текста для части 3/4:
                {structure_part}"""),
            expected_output=dedent(f"""\
                Полноценная третья часть статьи для dzen.ru:
                - ТОЧНО сохранить структуру раздела part 3
                - Добавить расширенные данные из базы знаний
                - Обязательные элементы:
                  * Углубленный анализ темы
                  * Конкретные кейсы и цифры
                - Формат:
                  * Логическая связь с предыдущими частями
                  * Причинно-следственная связь между абзацами
                  * Деловой стиль с экспертными терминами"""),
            agent=agent
        )
    
    def content_creation_task_part4(self, agent, structure_part):
        return Task(
            description=dedent(f"""\
                Строго придерживаться полученной структуры текста для части 4/4:
                {structure_part}"""),
            expected_output=dedent(f"""\
                Полноценная заключительная часть статьи для dzen.ru:
                - ТОЧНО сохранить структуру раздела part 4
                - Добавить завершающие данные из базы знаний
                - Обязательные элементы:
                  * Мощное заключение с выводом
                  * Призыв к действию или рефлексия
                - Формат:
                  * Логическое завершение всех частей
                  * Эмоциональная финальная нота
                  * Деловой стиль с элементами мотивации"""),
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
