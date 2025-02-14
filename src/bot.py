from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os
from dotenv import load_dotenv
from crewai import Crew
from .tasks import contentSocialMediaTasks
from .agents import contentSocialMediaAgents
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Привет! Я бот-ассистент Сергея Черненко. Я помогу вам создать контент для социальных сетей.\n\n'
        'Для начала работы, отправьте мне:\n'
        '1. Контекст или скрипт для поста\n'
        '2. Описание целевой аудитории\n\n'
        'Используйте команду /help для получения дополнительной информации.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        'Доступные команды:\n'
        '/start - Начать работу с ботом\n'
        '/help - Показать это сообщение\n\n'
        'Для создания контента просто отправьте мне текст с описанием того, что вы хотите создать.'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and generate content using CrewAI."""
    # Store user's message in context
    if 'messages' not in context.user_data:
        context.user_data['messages'] = []
    
    context.user_data['messages'].append(update.message.text)
    
    # If we have received both context and target audience
    if len(context.user_data['messages']) >= 2:
        await update.message.reply_text("Генерирую контент, пожалуйста подождите...")
        
        try:
            # Get the stored messages
            query_context = context.user_data['messages'][0]
            query_target_audience = context.user_data['messages'][1]
            
            # Create tasks and agents
            tasks = contentSocialMediaTasks()
            agents = contentSocialMediaAgents()
            
            # Initialize agents
            general_agent = agents.general_content_social_media_agent()
            editor_agent = agents.editor_social_media_agent()
            
            # Create tasks
            research_task = tasks.research_task(general_agent, query_context, query_target_audience)
            industry_analysis_task = tasks.industry_analysis_task(editor_agent, query_context, query_target_audience)
            
            # Set task context
            industry_analysis_task.context = [research_task]
            
            # Create and run crew
            crew = Crew(
                agents=[general_agent, editor_agent],
                tasks=[research_task, industry_analysis_task]
            )
            
            result = crew.kickoff()
            
            # Send the result back to user
            await update.message.reply_text(result)
            
            # Clear the stored messages
            context.user_data['messages'] = []
            
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            await update.message.reply_text(
                "Произошла ошибка при генерации контента. Пожалуйста, попробуйте еще раз."
            )
            context.user_data['messages'] = []
    else:
        await update.message.reply_text(
            "Теперь отправьте мне описание целевой аудитории."
        )

def main():
    """Start the bot."""
    load_dotenv()
    
    # Create the Application
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 