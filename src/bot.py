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
        'Здравствуйте! Я помогу вам создавать информативные комментарии для соцсетей.\n\n'
        'Чтобы начать, отправьте мне:\n'
        '1. Комментарий, на который хотите ответить\n'
        'Команда /help - если нужна помощь\n\n'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        'Как я работаю:\n'
        '/start - Начать работу\n'
        '/help - Показать это сообщение\n\n'
        'Отправьте комментарий и укажите соцсеть - я помогу составить информативный ответ'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and generate content using CrewAI."""
    if 'messages' not in context.user_data:
        context.user_data['messages'] = []
    
    context.user_data['messages'].append(update.message.text)
    
    if len(context.user_data['messages']) >= 2:
        await update.message.reply_text("Секундочку, формулирую ответ... ✍️")
        
        try:
            original_comment = context.user_data['messages'][0]
            social_platform = context.user_data['messages'][1]
            
            tasks = contentSocialMediaTasks()
            agents = contentSocialMediaAgents()
            
            general_agent = agents.general_content_social_media_agent()
            editor_agent = agents.editor_social_media_agent()
            
            research_task = tasks.research_task(general_agent, original_comment, social_platform)
            industry_analysis_task = tasks.industry_analysis_task(editor_agent, original_comment, social_platform)
            
            industry_analysis_task.context = [research_task]
            
            crew = Crew(
                agents=[general_agent, editor_agent],
                tasks=[research_task, industry_analysis_task]
            )
            
            result = crew.kickoff()
            
            # Debug: Print the result
            logger.info(f"Crew kickoff result: {result}")
            
            # The result appears to be the final text directly
            final_text = str(result)
            
            # Send the final text to Telegram
            await update.message.reply_text(final_text)
            
            context.user_data['messages'] = []
            
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            await update.message.reply_text(
                "Упс! Что-то пошло не так 😅 Давайте попробуем еще раз?"
            )
            context.user_data['messages'] = []
    else:
        await update.message.reply_text(
            "Отлично! Теперь укажите, из какой соцсети комментарий (например: ВКонтакте, Telegram, Дзен) 🌐"
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