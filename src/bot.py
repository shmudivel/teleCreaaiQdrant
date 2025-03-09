from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
import os
from dotenv import load_dotenv
from crewai import Crew
import logging
import asyncio
import sys

# Add the current directory to the Python path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use proper imports with src prefix
from src.platforms.factory import PlatformFactory
from src.text_splitter import split_text_into_parts
from src.utils.google_services import extract_doc_id, read_from_google_doc, save_to_google_drive

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        'Здравствуйте! Я помогу вам создавать информативные посты для соцсетей.\n\n'
        'Чтобы начать, отправьте мне:\n'
        '1. Ссылку на Google Doc с контентом\n'
        'Команда /help - если нужна помощь\n\n'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        'Как я работаю:\n'
        '/start - Начать работу\n'
        '/help - Показать это сообщение\n\n'
        'Отправьте ссылку на Google Doc с контентом - я помогу создать оптимизированный пост для выбранной соцсети'
    )

async def show_platform_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show buttons for platform selection."""
    platforms = PlatformFactory.get_available_platforms()
    
    keyboard = []
    for platform_id, display_name in platforms.items():
        keyboard.append([InlineKeyboardButton(display_name, callback_data=f"platform_{platform_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        'Выберите социальную сеть, для которой нужно создать пост:',
        reply_markup=reply_markup
    )

async def handle_platform_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle platform selection via callback query."""
    query = update.callback_query
    await query.answer()
    
    # Extract platform from callback data
    platform = query.data.replace("platform_", "")
    context.user_data['selected_platform'] = platform
    
    # Get the display name of the platform
    platforms = PlatformFactory.get_available_platforms()
    platform_name = platforms.get(platform, platform)
    
    await query.edit_message_text(f"Выбрана платформа: {platform_name}\n\nОтлично! Теперь я создам адаптированный пост из 4 частей... ✍️")
    
    # Process the content
    await process_content(update, context, query.message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and generate content using CrewAI."""
    if 'messages' not in context.user_data:
        context.user_data['messages'] = []
    
    current_message = update.message.text
    
    if len(context.user_data['messages']) == 0:
        # First message should be a Google Doc link
        doc_id = extract_doc_id(current_message)
        if not doc_id:
            await update.message.reply_text(
                "Пожалуйста, отправьте корректную ссылку на Google Doc с контентом 📄"
            )
            return
        
        # Read content from the Google Doc
        doc_content = read_from_google_doc(doc_id)
        if not doc_content:
            await update.message.reply_text(
                "Не удалось прочитать документ. Проверьте ссылку и права доступа 🔒"
            )
            return
        
        context.user_data['messages'].append(doc_content)
        
        # Show platform selection
        await show_platform_selection(update, context)

async def process_content(update: Update, context: ContextTypes.DEFAULT_TYPE, message=None):
    """Process the content for the selected platform."""
    from src.utils.content_processor import process_content_parts
    
    try:
        # Check if we have messages to process
        if not context.user_data.get('messages') or len(context.user_data['messages']) < 1:
            await update.message.reply_text("❌ Ошибка: Нет сообщения для обработки")
            return

        source_content = context.user_data['messages'][0]
        platform = context.user_data.get('selected_platform', 'dzen')  # Default to dzen if not specified
        
        # Split text into 4 parts
        content_parts = split_text_into_parts(source_content, 4)
        
        # Process content with helper function
        results = await process_content_parts(platform, content_parts, message or update.message)
        
        if results:
            # Reset user_data for next interaction
            context.user_data.clear()
    
    except Exception as e:
        logger.error(f"Error processing content: {str(e)}")
        if message:
            await message.reply_text(f"❌ Произошла ошибка при обработке контента: {str(e)}")
        else:
            await update.message.reply_text(f"❌ Произошла ошибка при обработке контента: {str(e)}")

def main():
    """Start the bot."""
    # Load environment variables
    load_dotenv()
    
    # Create the Application and pass your bot's token
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_platform_selection, pattern="^platform_"))
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main() 