from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler, ConversationHandler
import os
from dotenv import load_dotenv
from crewai import Crew
import logging
import asyncio
import sys
import traceback
import html
import requests
from pathlib import Path

# Add the current directory to the Python path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use proper imports with src prefix
from src.platforms.factory import PlatformFactory
from src.text_splitter import split_text_into_parts
from src.utils.google_services import extract_doc_id, read_from_google_doc, save_to_google_drive, save_telegram_message_to_sheet, get_telegram_messages, get_telegram_sheet_url, ensure_sheet_accessible

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define conversation states
(
    WAITING_FOR_URL, 
    WAITING_FOR_TRANSCRIPTION,
    WAITING_FOR_PLATFORM_SELECTION,
    WAITING_FOR_VECTOR_DB_QUERY
) = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    # Get user ID for logging
    user_id = update.effective_user.id
    logger.info(f"User {user_id} is starting a new session with /start command")
    
    # Clear user data to start fresh
    context.user_data.clear()
    
    # Send welcome message first
    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(
            'Здравствуйте! 👋\n\n'
            'Я помогу вам создавать посты для соцсетей и сохранять информацию в Google Sheets.\n'
            'Используйте кнопки ниже для взаимодействия со мной.'
        )
    
    # Show main menu with buttons
    await show_main_menu(update, context)
    
    # Log the start command
    asyncio.create_task(log_message_to_sheet(user_id, "/start (command)", "", True))
    
    # End any active conversation
    return ConversationHandler.END

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the main menu with available options."""
    keyboard = [
        [InlineKeyboardButton("Создать текстовый пост 📝", callback_data="menu_text_post")],
        [InlineKeyboardButton("Обновить Google Sheet 📊", callback_data="menu_update_sheet")],
        [InlineKeyboardButton("Задать вопрос Сергею 🗣️", callback_data="menu_vector_db")],
        [InlineKeyboardButton("Google Doc в YouTube 🎬", callback_data="menu_workflow")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = "Выберите действие:"
    
    # Handle either direct message or callback query
    if hasattr(update, 'message') and update.message:
        # Direct message - send new message
        await update.message.reply_text(message_text, reply_markup=reply_markup)
    elif hasattr(update, 'callback_query') and update.callback_query:
        # Callback query - edit existing message
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
    else:
        # Fallback for other update types
        logger.warning("Unknown update type in show_main_menu")
        return

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        'Я помогу вам создавать посты для соцсетей и сохранять информацию в Google Sheets.\n\n'
        'Доступные команды:\n'
        '/start - Начать работу с ботом\n'
        '/menu - Показать главное меню\n'
        '/restart - Сбросить текущую сессию и начать заново\n'
        '/help - Показать эту справку\n\n'
        'В главном меню доступны следующие опции:\n'
        '• Создать текстовый пост - создать пост для выбранной соцсети (Дзен, VC.ru)\n'
        '• Обновить Google Sheet - добавить запись в таблицу сообщений\n'
        '• Задать вопрос Сергею - получить ответ напрямую от Сергея Черненко на основе его знаний\n'
        '• Google Doc в YouTube - обработать документ для создания коротких видео для YouTube\n\n'
        'Для админов доступны дополнительные команды:\n'
        '/logs [число] - Показать последние записи из логов\n'
        '/sheet - Получить ссылку на Google Sheet с логами\n\n'
        'Возникли проблемы? Используйте команду /restart для сброса сессии.'
    )
    
    # Clear user data when showing help
    context.user_data.clear()
    
    return ConversationHandler.END

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu button selections."""
    query = update.callback_query
    
    try:
        await query.answer()
        
        selection = query.data
        user_id = update.effective_user.id
        
        if selection == "menu_text_post":
            # Text post creation flow
            await query.edit_message_text("Пожалуйста, отправьте ссылку на Google Doc с контентом 📄")
            context.user_data['flow'] = 'text_post'
            context.user_data['messages'] = []
            
            return WAITING_FOR_URL
            
        elif selection == "menu_update_sheet":
            # Update Google Sheet flow
            await query.edit_message_text(
                "Для обновления Google Sheet необходимо предоставить URL и транскрипцию.\n\n"
                "Пожалуйста, отправьте ссылку, которую нужно добавить в таблицу 🔗"
            )
            context.user_data['flow'] = 'update_sheet'
            
            return WAITING_FOR_URL
        
        elif selection == "menu_vector_db":
            # Vector DB query flow
            await query.edit_message_text(
                "Задайте вопрос Сергею Черненко, и он лично ответит вам 🗣️\n\n"
                "Что бы вы хотели узнать у Сергея? Спросите о карьере, развитии в найме, коммуникации с руководством - и Сергей поделится своим опытом."
            )
            context.user_data['flow'] = 'vector_db_query'
            
            return WAITING_FOR_VECTOR_DB_QUERY
            
        elif selection == "menu_workflow":
            # Google Doc to YouTube workflow - show two buttons for different workflows
            keyboard = [
                [InlineKeyboardButton("Генерация нескольких Reels с одного текста", callback_data="workflow_multiple_reels")],
                [InlineKeyboardButton("Генерация одного видео с одного текста", callback_data="workflow_single_video")],
                [InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Выберите тип генерации видео из Google Doc:",
                reply_markup=reply_markup
            )
            
            return ConversationHandler.END
            
        # Handle workflow selection buttons
        elif selection == "workflow_multiple_reels":
            # Original workflow for multiple reels
            await query.edit_message_text(
                "Пожалуйста, отправьте ссылку на Google Doc с контентом для создания нескольких YouTube видео 📄\n\n"
                "Документ будет обработан и разделен на короткие видеоролики для YouTube."
            )
            context.user_data['flow'] = 'google_doc_to_youtube'
            
            return WAITING_FOR_URL
            
        elif selection == "workflow_single_video":
            # New workflow for single video
            await query.edit_message_text(
                "Пожалуйста, отправьте ссылку на Google Doc с контентом для создания одного YouTube видео 📄\n\n"
                "Документ будет обработан для создания одного цельного видео."
            )
            context.user_data['flow'] = 'google_doc_to_single_video'
            
            return WAITING_FOR_URL
            
    except Exception as e:
        logger.error(f"Error handling menu selection: {str(e)}")
        await query.message.reply_text(f"❌ Произошла ошибка: {str(e)}")
        return ConversationHandler.END

async def handle_url_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle URL input based on the selected flow."""
    user_id = update.effective_user.id
    text = update.message.text
    
    if context.user_data.get('flow') == 'text_post':
        # Text post flow - validate Google Doc URL
        doc_id = extract_doc_id(text)
        if not doc_id:
            await update.message.reply_text(
                "Пожалуйста, отправьте корректную ссылку на Google Doc с контентом 📄"
            )
            return WAITING_FOR_URL
        
        # Read content from Google Doc
        doc_content = read_from_google_doc(doc_id)
        if not doc_content:
            await update.message.reply_text(
                "Не удалось прочитать документ. Проверьте ссылку и права доступа 🔒"
            )
            return WAITING_FOR_URL
        
        context.user_data['messages'] = [doc_content]
        
        # Show platform selection for text post
        await show_text_post_platforms(update, context)
        return WAITING_FOR_PLATFORM_SELECTION
        
    elif context.user_data.get('flow') == 'update_sheet':
        # Update Sheet flow - store URL and ask for transcription
        context.user_data['url'] = text
        await update.message.reply_text(
            "Спасибо! Теперь отправьте транскрипцию или описание для этой ссылки 📝"
        )
        return WAITING_FOR_TRANSCRIPTION
    
    elif context.user_data.get('flow') == 'google_doc_to_youtube':
        # Google Doc to YouTube flow - validate Google Doc URL
        doc_id = extract_doc_id(text)
        if not doc_id:
            await update.message.reply_text(
                "Пожалуйста, отправьте корректную ссылку на Google Doc с контентом 📄"
            )
            return WAITING_FOR_URL
        
        # Process the document for YouTube workflow
        await process_google_doc_for_youtube(update, context, text)
        
        # End the conversation after starting the workflow
        return ConversationHandler.END
    
    elif context.user_data.get('flow') == 'google_doc_to_single_video':
        # Single video flow - validate Google Doc URL
        doc_id = extract_doc_id(text)
        if not doc_id:
            await update.message.reply_text(
                "Пожалуйста, отправьте корректную ссылку на Google Doc с контентом 📄"
            )
            return WAITING_FOR_URL
        
        # Show coming soon message
        keyboard = [
            [InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔜 Функция генерации одного видео находится в разработке и будет доступна в ближайшее время!\n\n"
            "Пока вы можете использовать функцию генерации нескольких коротких видео.",
            reply_markup=reply_markup
        )
        
        # End the conversation after showing the message
        return ConversationHandler.END
    
    # Fallback for unexpected flow state
    await update.message.reply_text("Что-то пошло не так. Пожалуйста, начните сначала с команды /start")
    return ConversationHandler.END

async def handle_transcription_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when the user sends a message to transcribe."""
    user_id = update.effective_user.id
    message_text = update.message.text
    url = context.user_data.get('url', '')
    
    # Validate that both URL and transcription are provided
    if not url:
        await update.message.reply_text(
            "❌ Отсутствует URL. Пожалуйста, начните процесс обновления Google Sheet заново, используя соответствующий пункт меню."
        )
        # Clear user data if validation fails
        context.user_data.clear()
        return ConversationHandler.END
        
    if not message_text:
        await update.message.reply_text(
            "❌ Отсутствует транскрипция. Пожалуйста, отправьте текст транскрипции."
        )
        return WAITING_FOR_TRANSCRIPTION
    
    # Log the received transcription
    logger.info(f"Received transcription from user {user_id}: {message_text[:30]}...")
    
    # Send processing message
    processing_message = await update.message.reply_text("⏳ Обрабатываю вашу запись и добавляю в таблицу...")
    
    try:
        # Run the save operation in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: save_telegram_message_to_sheet(user_id, message_text, url)
        )
        
        if result.get('success'):
            # Get links information
            sheet_url = result.get('sheet_url', '')
            
            # Create success message - simplified version
            success_message = "✅ Запись успешно добавлена в Google Sheet!\n\n"
            
            # Add buttons for the next action
            keyboard = [
                [InlineKeyboardButton("➕ Добавить еще запись", callback_data="add_another_record")],
                [InlineKeyboardButton("🏠 Вернуться в меню", callback_data="menu_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Edit the processing message with the success message
            await processing_message.edit_text(success_message, reply_markup=reply_markup)
            
        else:
            error = result.get('error', 'Неизвестная ошибка')
            await processing_message.edit_text(
                f"❌ Ошибка при сохранении данных в таблицу: {error}\n\n"
                "Пожалуйста, попробуйте еще раз или обратитесь к администратору."
            )
    except Exception as e:
        logger.error(f"Error in handle_transcription_input: {str(e)}")
        await processing_message.edit_text(
            f"❌ Произошла ошибка: {str(e)}\n\n"
            "Пожалуйста, попробуйте еще раз или обратитесь к администратору."
        )
    
    # Clear user data upon completion (success or failure)
    context.user_data.clear()
    
    # Return to the main conversation handler
    return ConversationHandler.END

async def add_structured_record_to_sheet(user_id, url, transcription, context):
    """Add a structured record to the Google Sheet with metadata."""
    try:
        # Validate input parameters
        if not url or not transcription:
            logger.warning(f"Failed to add record: Missing URL or transcription from user {user_id}")
            return {
                'success': False, 
                'error': 'Missing required URL or transcription for Google Sheet update'
            }
            
        from datetime import datetime
        
        # Create a structured message with metadata
        structured_message = f"""URL: {url}
        
TRANSCRIPTION:
{transcription}

Added via Telegram Bot at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        # Run in executor to prevent blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: save_telegram_message_to_sheet(user_id, structured_message, url)
        )
        
        if result and result.get('success'):
            logger.info(f"Successfully added structured record from user {user_id} to Google Sheet")
            logger.info(f"Spreadsheet URL: {result.get('sheet_url')}")
            logger.info(f"Spreadsheet ID: {result.get('spreadsheet_id')}")
            return result
        else:
            error = result.get('error', 'Unknown error') if result else 'Unknown error'
            logger.warning(f"Failed to add structured record from user {user_id} to Google Sheet: {error}")
            return result or {'success': False, 'error': 'Unknown error'}
            
    except Exception as e:
        logger.error(f"Error in add_structured_record_to_sheet: {str(e)}")
        return {'success': False, 'error': str(e)}

async def show_text_post_platforms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show buttons for text post platform selection."""
    # Define which platforms to show
    text_platforms = {
        "dzen": "Дзен",
        "vc": "VC.ru"
    }
    
    keyboard = []
    for platform_id, display_name in text_platforms.items():
        keyboard.append([InlineKeyboardButton(display_name, callback_data=f"platform_{platform_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        'Выберите платформу, для которой нужно создать пост:',
        reply_markup=reply_markup
    )
    
    # Log platform selection request
    user_id = update.effective_user.id
    asyncio.create_task(log_message_to_sheet(user_id, "[BOT] Text platform selection request", "", True))

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation and return to start."""
    await update.message.reply_text("Операция отменена. Используйте /start для начала.")
    return ConversationHandler.END

async def end_conversation_and_reset(update: Update, context: ContextTypes.DEFAULT_TYPE, message=None, reply_markup=None):
    """Utility function to properly end a conversation and reset user state.
    
    Args:
        update: The update object
        context: The context object
        message: Optional message to send to the user
        reply_markup: Optional reply markup to include with the message
        
    Returns:
        ConversationHandler.END to properly end the conversation
    """
    # Clear user data
    context.user_data.clear()
    
    # Send message if provided
    if message:
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(message, reply_markup=reply_markup)
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    
    # Log conversation end
    user_id = update.effective_user.id if update.effective_user else "unknown"
    logger.info(f"Ending conversation and resetting state for user {user_id}")
    
    # Return END to properly end the conversation
    return ConversationHandler.END

async def handle_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'Back to menu' button click."""
    query = update.callback_query
    
    try:
        # Make sure to answer the callback query
        await query.answer("Возвращаемся в главное меню")
        
        user_id = update.effective_user.id
        logger.info(f"User {user_id} clicked 'Back to menu' button with callback_data: {query.data}")
        
        # Reset user data
        context.user_data.clear()
        
        # Edit the current message to remove buttons
        try:
            await query.edit_message_text(
                text="Возвращаемся в главное меню...",
                reply_markup=None
            )
            logger.info(f"Successfully edited message for user {user_id}")
        except Exception as edit_error:
            logger.error(f"Error editing message: {str(edit_error)}")
        
        # Show main menu - using the same function as /start command
        await show_main_menu(update, context)
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error returning to menu: {str(e)}")
        try:
            await query.message.reply_text("Используйте /start для возврата в главное меню.")
        except:
            logger.error("Failed to send fallback message")
        # Make sure to clear context data even on error
        context.user_data.clear()
        return ConversationHandler.END

async def handle_platform_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle platform selection via callback query."""
    query = update.callback_query
    
    try:
        # Try to answer the callback query, but don't fail if it's already been answered
        try:
            await query.answer()
        except Exception as e:
            logger.warning(f"Could not answer callback query: {str(e)}")
    
        # Extract platform from callback data
        platform = query.data.replace("platform_", "")
        context.user_data['selected_platform'] = platform
        
        # Get the display name of the platform
        if platform == "dzen":
            platform_name = "Дзен"
        elif platform == "vc":
            platform_name = "VC.ru"
        else:
            platforms = PlatformFactory.get_available_platforms()
            platform_name = platforms.get(platform, platform)
        
        # Log platform selection
        user_id = update.effective_user.id
        asyncio.create_task(log_message_to_sheet(
            user_id, 
            f"[SELECTION] Selected platform: {platform_name}", 
            "", True
        ))
        
        try:
            await query.edit_message_text(f"Выбрана платформа: {platform_name}\n\nОтлично! Теперь я создам адаптированный пост из 4 частей... ✍️")
        except Exception as e:
            logger.warning(f"Could not edit message text: {str(e)}")
            # If we can't edit the original message, send a new one
            await query.message.reply_text(f"Выбрана платформа: {platform_name}\n\nОтлично! Теперь я создам адаптированный пост из 4 частей... ✍️")
        
        # Process the content
        await process_content(update, context, query.message)
        
        # End the conversation
        return ConversationHandler.END
    
    except Exception as e:
        error_msg = f"Ошибка при обработке выбора платформы: {str(e)}"
        logger.error(error_msg)
        try:
            await query.message.reply_text(f"❌ {error_msg}")
        except Exception:
            # Last resort if everything fails
            pass
        return ConversationHandler.END

async def process_content(update: Update, context: ContextTypes.DEFAULT_TYPE, message=None):
    """Process the content for the selected platform."""
    from src.utils.content_processor import process_content_parts
    
    try:
        # Check if we have messages to process
        if not context.user_data.get('messages') or len(context.user_data['messages']) < 1:
            if message:
                await message.reply_text("❌ Ошибка: Нет сообщения для обработки")
            else:
                await update.message.reply_text("❌ Ошибка: Нет сообщения для обработки")
            return

        source_content = context.user_data['messages'][0]
        platform = context.user_data.get('selected_platform', 'dzen')  # Default to dzen if not specified
        
        # Split text into 4 parts
        content_parts = split_text_into_parts(source_content, 4)
        
        # Process content with helper function
        results = await process_content_parts(platform, content_parts, message or update.message)
        
        if results:
            # After successful processing, give option to return to main menu
            keyboard = [
                [InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if message:
                await message.reply_text("Что делаем дальше?", reply_markup=reply_markup)
            else:
                await update.message.reply_text("Что делаем дальше?", reply_markup=reply_markup)
            
            # Reset user_data for next interaction except for essential items
            if 'messages' in context.user_data:
                del context.user_data['messages']
            if 'selected_platform' in context.user_data:
                del context.user_data['selected_platform']
    
    except Exception as e:
        logger.error(f"Error processing content: {str(e)}")
        if message:
            await message.reply_text(f"❌ Произошла ошибка при обработке контента: {str(e)}")
        else:
            await update.message.reply_text(f"❌ Произошла ошибка при обработке контента: {str(e)}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the developer."""
    # Log the error before we do anything else
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python exception information as a list
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with escaped HTML tags so it looks nice
    message = (
        f"An exception occurred while processing an update\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Store the message in bot_data
    if "error_messages" not in context.bot_data:
        context.bot_data["error_messages"] = []
    context.bot_data["error_messages"].append(message)
    
    # If this was a user-triggered update, notify them
    try:
        if update and hasattr(update, 'effective_message') and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Извините, произошла ошибка при обработке запроса. Попробуйте позже."
            )
            
            # Log error to sheet if possible
            if hasattr(update, 'effective_user') and update.effective_user:
                user_id = update.effective_user.id
                error_msg = str(context.error)[:200] + "..." if len(str(context.error)) > 200 else str(context.error)
                asyncio.create_task(log_message_to_sheet(
                    user_id,
                    f"[ERROR] {error_msg}",
                    "", True
                ))
    except Exception as e:
        logger.error(f"Error in error handler while sending message: {str(e)}")

async def log_message_to_sheet(user_id, text, url=None, user_consent=False):
    """Log message to Google Sheets without blocking the bot."""
    try:
        # Only proceed if user explicitly gave consent or this is a system log
        if not user_consent and not text.startswith("[BOT]") and not text.endswith("(command)"):
            logger.info(f"Skipping Google Sheet logging for user {user_id} - no explicit consent given")
            return {'success': False, 'error': 'User did not explicitly consent to Google Sheet update'}
            
        # Run in executor to prevent blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            lambda: save_telegram_message_to_sheet(user_id, text, url)
        )
        if result:
            logger.info(f"Successfully logged message from user {user_id} to Google Sheets")
        else:
            logger.warning(f"Failed to log message from user {user_id} to Google Sheets")
    except Exception as e:
        logger.error(f"Error in log_message_to_sheet: {str(e)}")

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send recent message logs to admin users."""
    # Check if user is admin
    admin_ids = [
        1234567890,  # Replace with your actual admin user IDs
        int(os.getenv("ADMIN_USER_ID", "0"))  # Get from env var if set
    ]
    
    user_id = update.effective_user.id
    if user_id not in admin_ids and str(user_id) != os.getenv("ADMIN_USER_ID", "0"):
        await update.message.reply_text("⛔ Извините, у вас нет доступа к этой команде.")
        return
    
    # Parse arguments (number of logs to retrieve)
    args = context.args
    limit = 10  # Default limit
    
    if args and args[0].isdigit():
        limit = min(int(args[0]), 50)  # Cap at 50 to avoid message size issues
    
    await update.message.reply_text(f"Получение последних {limit} сообщений из логов...")
    
    # Get logs in background
    asyncio.create_task(retrieve_and_send_logs(update, limit))
    
    # Log command usage
    asyncio.create_task(log_message_to_sheet(user_id, f"/logs {limit} (command)", "", True))

async def retrieve_and_send_logs(update, limit):
    """Retrieve logs and send them to the chat."""
    try:
        # Get logs from Google Sheets
        loop = asyncio.get_event_loop()
        logs = await loop.run_in_executor(
            None, 
            lambda: get_telegram_messages(limit=limit)
        )
        
        if not logs:
            await update.message.reply_text("❌ Не удалось получить логи или логи отсутствуют.")
            return
        
        # Format logs as text
        response = f"📊 Последние {len(logs)} записей из логов (сначала новые):\n\n"
        
        for i, log in enumerate(logs):
            # Get first 30 chars of text
            text_preview = log.get('Text', '')[:30] + ('...' if len(log.get('Text', '')) > 30 else '')
            
            response += f"{i+1}. User: {log.get('User ID')}\n"
            response += f"   Time: {log.get('Timestamp')}\n"
            response += f"   Text: {text_preview}\n"
            
            if log.get('URL'):
                response += f"   URL: {log.get('URL')}\n"
            
            response += "\n"
        
        # Send response, splitting if needed
        if len(response) > 4000:
            # Split into chunks
            for i in range(0, len(response), 4000):
                chunk = response[i:i+4000]
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(response)
            
    except Exception as e:
        logger.error(f"Error retrieving logs: {str(e)}")
        await update.message.reply_text(f"❌ Ошибка при получении логов: {str(e)}")

async def sheet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the URL of the message logs spreadsheet to admin users."""
    # Check if user is admin
    admin_ids = [
        1234567890,  # Replace with your actual admin user IDs
        int(os.getenv("ADMIN_USER_ID", "0"))  # Get from env var if set
    ]
    
    user_id = update.effective_user.id
    if user_id not in admin_ids and str(user_id) != os.getenv("ADMIN_USER_ID", "0"):
        await update.message.reply_text("⛔ Извините, у вас нет доступа к этой команде.")
        return
    
    await update.message.reply_text("Получение информации о таблице и настройка доступа...")
    
    # Get spreadsheet URL in background
    asyncio.create_task(retrieve_and_send_sheet_url(update, fix_access=True))
    
    # Log command usage
    asyncio.create_task(log_message_to_sheet(user_id, "/sheet (command)", "", True))

async def retrieve_and_send_sheet_url(update, fix_access=False):
    """Retrieve the spreadsheet URL and send it to the chat."""
    try:
        # Get spreadsheet URL
        loop = asyncio.get_event_loop()
        sheet_info = await loop.run_in_executor(
            None, 
            get_telegram_sheet_url
        )
        
        if not sheet_info or not sheet_info.get('success'):
            error_msg = sheet_info.get('error', 'Неизвестная ошибка') if sheet_info else 'Таблица не найдена'
            await update.message.reply_text(
                f"❌ Не удалось получить информацию о таблице: {error_msg}\n\n"
                "Возможно, таблица еще не создана. Чтобы создать таблицу, выберите в меню 'Обновить Google Sheet' и добавьте первую запись."
            )
            return
        
        # Fix access permissions if requested
        access_info = None
        if fix_access:
            spreadsheet_id = sheet_info.get('spreadsheet_id')
            if spreadsheet_id:
                await update.message.reply_text("🔄 Настраиваю доступ к таблице...")
                
                # Ensure the sheet is accessible
                access_info = await loop.run_in_executor(
                    None,
                    lambda: ensure_sheet_accessible(spreadsheet_id)
                )
                
                if access_info and access_info.get('success'):
                    await update.message.reply_text("✅ Доступ к таблице успешно настроен!")
                else:
                    await update.message.reply_text("⚠️ Возникли проблемы при настройке доступа к таблице.")
        
        # Format the sheet information
        sheet_url = sheet_info.get('url', '')
        spreadsheet_id = sheet_info.get('spreadsheet_id', '')
        owner = sheet_info.get('owner', 'Неизвестно')
        created = sheet_info.get('created', 'Неизвестно').replace('T', ' ').replace('Z', '')[:19] if 'T' in sheet_info.get('created', '') else sheet_info.get('created', 'Неизвестно')
        modified = sheet_info.get('modified', 'Неизвестно').replace('T', ' ').replace('Z', '')[:19] if 'T' in sheet_info.get('modified', '') else sheet_info.get('modified', 'Неизвестно')
        
        shared_with = []
        for user in sheet_info.get('shared_with', []):
            shared_with.append(f"- {user.get('email', '')} ({user.get('role', '')})")
            
        sheets_info = []
        for sheet in sheet_info.get('sheets', []):
            sheets_info.append(f"- {sheet.get('title', '')}: {sheet.get('rows', 0)} строк")
        
        # Create detailed message
        message = "📊 Информация о таблице сообщений:\n\n"
        message += f"📝 Название: {sheet_info.get('name', '')}\n"
        message += f"🔗 Ссылка на таблицу: {sheet_url}\n"
        message += f"🆔 ID таблицы: {spreadsheet_id}\n"
        message += f"👤 Владелец: {owner}\n"
        message += f"📅 Создано: {created}\n"
        message += f"🕒 Изменено: {modified}\n\n"
        
        if shared_with:
            message += "👥 Общий доступ предоставлен:\n"
            message += "\n".join(shared_with)
            message += "\n\n"
        else:
            message += "⚠️ Общий доступ не предоставлен никому!\n\n"
        
        # Add sharing links if available
        if fix_access and access_info and access_info.get('success'):
            message += "🛠 Дополнительно настроен доступ:\n"
            
            # Show all successful methods
            successful_methods = [r for r in access_info.get('results', []) if r.get('success')]
            if successful_methods:
                for method in successful_methods:
                    if method.get('details', {}).get('type') == 'user':
                        message += "- Доступ для пользователя ✅\n"
                    elif method.get('details', {}).get('type') == 'domain':
                        message += "- Доступ для домена ✅\n"
                    elif method.get('details', {}).get('type') == 'anyone':
                        if method.get('details', {}).get('role') == 'writer':
                            message += "- Доступ по ссылке (редактирование) ✅\n"
                        else:
                            message += "- Доступ по ссылке (просмотр) ✅\n"
            
            # Add direct sharing links
            sharing_links = access_info.get('sharing_links', {})
            if sharing_links:
                message += "\n📎 Ссылки для общего доступа:\n"
                
                if sharing_links.get('edit_link'):
                    message += f"📝 Ссылка для редактирования:\n{sharing_links.get('edit_link')}\n\n"
                
                if sharing_links.get('view_link'):
                    message += f"👁 Ссылка для просмотра:\n{sharing_links.get('view_link')}\n\n"
            else:
                message += "\n"
        
        if sheets_info:
            message += "📑 Листы в таблице:\n"
            message += "\n".join(sheets_info)
            message += "\n\n"
            
        message += f"🔍 Прямая ссылка для поиска в Google Drive:\n{sheet_info.get('drive_url', '')}\n\n"
        
        # Add access instructions
        message += "ℹ️ Инструкции по доступу:\n"
        message += "1. Таблица должна быть доступна для shmudivel@gmail.com\n"
        message += "2. Если вы видите сообщение 'You need access':\n"
        message += "   • Убедитесь, что вы вошли в аккаунт shmudivel@gmail.com\n"
        message += "   • Выйдите из других аккаунтов Google или используйте режим инкогнито\n"
        message += "3. Если проблемы с доступом сохраняются, выполните следующие действия:\n"
        message += "   • Используйте команду /sheet для повторной настройки доступа\n"
        message += "   • Выберите в боте пункт 'Обновить Google Sheet' и добавьте запись\n"
        
        # Add buttons
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить доступ к таблице", callback_data="refresh_sheet_access")],
            [InlineKeyboardButton("🏠 Вернуться в меню", callback_data="menu_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Error retrieving sheet URL: {str(e)}")
        await update.message.reply_text(f"❌ Ошибка при получении ссылки на таблицу: {str(e)}")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the main menu when the user sends /menu command."""
    keyboard = [
        [InlineKeyboardButton("Создать текстовый пост 📝", callback_data="menu_text_post")],
        [InlineKeyboardButton("Обновить Google Sheet 📊", callback_data="menu_update_sheet")],
        [InlineKeyboardButton("Задать вопрос Сергею 🗣️", callback_data="menu_vector_db")],
        [InlineKeyboardButton("Google Doc в YouTube 🎬", callback_data="menu_workflow")],
        [InlineKeyboardButton("Посмотреть логи 🔍", callback_data="menu_logs")],
        [InlineKeyboardButton("Получить ссылку на таблицу 📊", callback_data="menu_sheet")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Главное меню бота:",
        reply_markup=reply_markup
    )

async def handle_unknown_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unexpected or unknown inputs during conversations."""
    await update.message.reply_text(
        "Извините, я не понимаю этот ввод. Пожалуйста, следуйте инструкциям или используйте /menu для возврата в главное меню."
    )
    
    # Don't end the conversation, let the user try again
    return

async def refresh_sheet_access_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the refresh sheet access button click."""
    query = update.callback_query
    await query.answer()
    
    # Get the chat where the button was pressed
    chat_id = update.effective_chat.id
    
    # Let the user know we're working on it
    await query.edit_message_text(
        text=f"🔄 Обновляю доступ к таблице...\n\nЭто может занять несколько секунд.",
        reply_markup=None
    )
    
    # Create a fake update object to pass to retrieve_and_send_sheet_url
    class FakeMessage:
        def __init__(self, chat_id):
            self.chat_id = chat_id
            
        async def reply_text(self, text, reply_markup=None):
            return await context.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                reply_markup=reply_markup
            )
    
    class FakeUpdate:
        def __init__(self, chat_id):
            self.message = FakeMessage(chat_id)
            
    fake_update = FakeUpdate(chat_id)
    
    # Run the sheet URL retrieval with access fixing
    await retrieve_and_send_sheet_url(fake_update, fix_access=True)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callbacks from menu buttons."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "add_another_record":
        # Set the flow to update sheet again
        context.user_data['flow'] = 'update_sheet'
        
        # Edit the message to ask for URL
        await query.edit_message_text(
            text="Пожалуйста, отправьте ссылку, которую нужно добавить в таблицу 🔗",
            reply_markup=None
        )
        
        # Return to the URL input state
        return WAITING_FOR_URL

async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown text messages."""
    
    # Default message for unrecognized input
    message = "🤔 Я не понимаю это сообщение. Пожалуйста, воспользуйтесь командами:\n\n/start - Начать работу с ботом\n/menu - Показать главное меню\n/help - Показать справку"
    
    # Suggest using the /menu command
    await update.message.reply_text(message)
    
    return ConversationHandler.END

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callbacks from the main menu buttons."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "menu_logs":
        # Edit message to acknowledge selection
        await query.edit_message_text("Получение логов...")
        
        # Create a fake update to pass to logs_command
        class FakeUpdate:
            def __init__(self, effective_user, message=None):
                self.effective_user = effective_user
                self.message = message
                
        fake_update = FakeUpdate(query.from_user, message=query.message)
        fake_update.message.reply_text = query.message.reply_text
        
        # Call logs command
        await logs_command(fake_update, context)
        return ConversationHandler.END
        
    elif data == "menu_sheet":
        # Edit message to acknowledge selection
        await query.edit_message_text("Получение информации о таблице...")
        
        # Create a fake update to pass to sheet_command
        class FakeUpdate:
            def __init__(self, effective_user, message=None):
                self.effective_user = effective_user
                self.message = message
                
        fake_update = FakeUpdate(query.from_user, message=query.message)
        fake_update.message.reply_text = query.message.reply_text
        
        # Call sheet command
        await sheet_command(fake_update, context)
        return ConversationHandler.END

async def handle_vector_db_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user queries to the vector database."""
    user_id = update.effective_user.id
    query_text = update.message.text
    
    if not query_text:
        await update.message.reply_text("Пожалуйста, введите вопрос для Сергея Черненко.")
        return WAITING_FOR_VECTOR_DB_QUERY
    
    logger.info(f"Received question for Sergey from user {user_id}: '{query_text}'")
    
    # Send processing message
    processing_message = await update.message.reply_text("⏳ Сергей обдумывает ваш вопрос...")
    
    try:
        # Import the VectorDBIntegration
        from src.platforms.vector_db import VectorDBIntegration
        
        # Log the start of vector retrieval process
        logger.info(f"Starting vector database retrieval and processing for query: '{query_text}'")
        
        # Create integration instance
        integration = VectorDBIntegration(
            collection_name="context-main3", 
            top_k=5,
            max_iterations=3,
            process_timeout=180  # 3 minutes timeout
        )
        
        # Process the query with integrated vector retrieval and agent processing
        logger.info("Processing query with VectorDBIntegration")
        result = integration.process_query(query_text)
        
        # Ensure result is a string
        if result is None:
            result = "Извините, не удалось сформировать ответ. Пожалуйста, задайте вопрос по-другому."
            logger.warning("Received None result from VectorDBIntegration")
        else:
            result_text = str(result)
            logger.info(f"Vector retrieval and agent processing completed, result length: {len(result_text)}")
            result = result_text
        
        # Update the processing message with the result
        await processing_message.edit_text(f"{result}")
        
        # Show back to menu button
        keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data="menu_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Что хотите сделать дальше?", reply_markup=reply_markup)
        
        # Clear user data before ending conversation
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error processing vector DB query: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Provide more specific error message based on the exception type
        error_message = "❌ Произошла ошибка при обработке запроса"
        
        if "all messages must have non-empty content" in str(e):
            error_message += ": Получен пустой ответ от инструмента. Пожалуйста, попробуйте задать более конкретный вопрос."
        elif "field required" in str(e).lower():
            error_message += ": Ошибка в формате запроса. Мы работаем над исправлением проблемы."
        elif "CrewOutput" in str(e):
            error_message += ": Ошибка в формате ответа от AI. Мы работаем над исправлением проблемы."
        else:
            error_message += f": {str(e)}"
        
        # Send error message to the user
        await processing_message.edit_text(error_message)
        
        # Still show back to menu button
        keyboard = [[InlineKeyboardButton("Вернуться в меню", callback_data="menu_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Хотите вернуться в меню?", reply_markup=reply_markup)
        
        # Clear user data even on error
        context.user_data.clear()
        
        return ConversationHandler.END

async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force reset user state and restart the bot conversation.
    This command is useful when a user gets stuck in a workflow."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} is restarting their session with /restart command")
    
    # Clear all user data
    context.user_data.clear()
    
    # Send message to user
    await update.message.reply_text(
        "🔄 Ваша сессия сброшена. Теперь вы можете начать новый рабочий процесс."
    )
    
    # Show main menu
    await show_main_menu(update, context)
    
    return ConversationHandler.END

async def process_google_doc_for_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE, doc_url: str):
    """Process a Google Doc for YouTube videos using the workflow platform."""
    # Send processing message
    processing_message = await update.message.reply_text("⏳ Обрабатываю документ и создаю видеоролики. Это может занять некоторое время...")
    
    try:
        # Get the workflow tasks
        from src.platforms.factory import PlatformFactory
        workflow_tasks = PlatformFactory.get_platform_tasks("workflow")
        
        # Create a timestamp-based output directory
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"output_{timestamp}"
        
        # Log process start
        logger.info(f"Starting Google Doc to YouTube workflow for {doc_url} with output to {output_dir}")
        
        # Process the document in a background task
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: workflow_tasks.google_doc_to_reels_task(doc_url, output_dir)
        )
        
        # Process completed
        if result:
            # Get the optimized scripts directory instead of final reels directory
            optimized_dir = result.get("optimized_dir", "")
            
            # Create success message
            success_message = (
                "✅ Обработка документа завершена успешно!\n\n"
                f"📂 Оптимизированные скрипты сохранены в: {optimized_dir}\n\n"
                "Процесс создал следующие материалы:\n"
                "1. Проанализированный документ\n"
                "2. Сценарии для коротких видео\n"
                "3. Отобраны самые потенциально вирусные ролики\n"
                "4. Финальные отредактированные и оптимизированные сценарии с SSML тегами"
            )
            
            # Update the processing message
            await processing_message.edit_text(success_message)
            
            # Load the optimized reels to present for selection
            try:
                import os
                import json
                
                # Use optimized directory as the source for reels
                reels_source_dir = optimized_dir
                
                # Verify directory exists
                if not os.path.exists(reels_source_dir):
                    raise FileNotFoundError(f"Directory not found: {reels_source_dir}")
                
                # Create a list to store reel information
                reels = []
                
                # Load all optimized reel JSON files
                for filename in os.listdir(reels_source_dir):
                    if filename.endswith('.json') and filename.startswith('optimized_'):
                        file_path = os.path.join(reels_source_dir, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                # Ensure the loaded JSON has the required heygen_script
                                if 'heygen_script' in data:
                                    reels.append({
                                        'path': file_path,
                                        'data': data,
                                        'filename': filename
                                    })
                                else:
                                    logger.warning(f"Skipping {filename}: missing 'heygen_script' key")
                        except Exception as e:
                            logger.error(f"Error loading {filename}: {e}")
                
                # Sort reels by index in filename (try to extract number after first underscore)
                try:
                    reels.sort(key=lambda x: int(os.path.basename(x['filename']).split('_')[1]))
                except (IndexError, ValueError):
                    # Fallback if filename format is different
                    logger.warning("Could not sort reels by index, using filename order instead")
                    reels.sort(key=lambda x: x['filename'])
                
                # Check if we have reels to display
                if reels:
                    # Store reels in user_data for callback handling
                    context.user_data['reels'] = reels
                    # Store both keys for backward compatibility
                    context.user_data['reels_source_dir'] = reels_source_dir
                    context.user_data['final_reels_dir'] = reels_source_dir  # for backward compatibility
                    
                    # Create inline buttons for each reel
                    keyboard = []
                    for i, reel in enumerate(reels, 1):
                        title = reel['data'].get('title', f'Ролик {i}')
                        # Limit title length to avoid button overflow
                        if len(title) > 40:
                            title = title[:37] + "..."
                        keyboard.append([InlineKeyboardButton(f"{i}. {title}", callback_data=f"reel_{i-1}")])
                    
                    # Add back button
                    keyboard.append([InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")])
                    
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        "Выберите оптимизированный сценарий для генерации аудио, а затем видео в HeyGen:",
                        reply_markup=reply_markup
                    )
                else:
                    # No reels found
                    await update.message.reply_text(
                        "❌ Не найдено ни одного оптимизированного сценария в указанной директории.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")
                        ]])
                    )
            except Exception as e:
                logger.error(f"Error loading optimized scripts for selection: {str(e)}")
                # Show menu button as fallback
                keyboard = [
                    [InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(f"Произошла ошибка при загрузке оптимизированных сценариев: {str(e)}", reply_markup=reply_markup)
        else:
            # Error occurred
            await processing_message.edit_text(
                "❌ Произошла ошибка при обработке документа. Пожалуйста, проверьте логи и попробуйте снова."
            )
    
    except Exception as e:
        logger.error(f"Error in process_google_doc_for_youtube: {str(e)}")
        # Update the processing message with error
        await processing_message.edit_text(
            f"❌ Произошла ошибка при обработке документа: {str(e)}\n\n"
            "Пожалуйста, проверьте, что документ доступен и повторите попытку."
        )

async def handle_reel_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the selection of a reel for processing with HeyGen and uploading to YouTube."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Get the selected reel index from the callback data
        reel_idx = int(query.data.split('_')[1])
        
        # Get the reels list from user_data
        reels = context.user_data.get('reels', [])
        # final_reels_dir is the 'optimized_dir' from the workflow, used as base for audio_previews
        final_reels_dir = context.user_data.get('final_reels_dir') # This is effectively optimized_dir

        if not reels or reel_idx >= len(reels):
            await query.edit_message_text(
                "❌ Выбранный ролик не найден. Пожалуйста, попробуйте снова.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")
                ]])
            )
            return

        if not final_reels_dir: # This is the optimized_scripts directory
            logger.error("final_reels_dir (optimized_scripts_dir) not found in user_data for audio generation.")
            await query.edit_message_text(
                "❌ Ошибка: не удалось определить директорию для аудиофайла. Пожалуйста, попробуйте снова.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")
                ]])
            )
            return

        # Get the selected reel metadata
        selected_reel_metadata = reels[reel_idx]['data']
        title = selected_reel_metadata.get('title', 'Без названия')
        heygen_script = selected_reel_metadata.get('heygen_script', '')

        if not heygen_script:
            logger.error(f"No heygen_script found for reel: {title}")
            await query.edit_message_text(
                f"❌ Ошибка: отсутствует оптимизированный скрипт для ролика '{title}'. Невозможно сгенерировать аудио.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")
                ]])
            )
            return
        
        # Update the message to show audio generation status
        await query.edit_message_text(f"⏳ Генерирую аудио превью для '{title}' с помощью ElevenLabs и нарезаю его...")

        # audio_preview_dir is where the main .mp3 and its parts/ subdir will go.
        # It should be inside final_reels_dir (which is optimized_scripts)
        audio_preview_base_dir = os.path.join(final_reels_dir, "audio_previews")
        Path(audio_preview_base_dir).mkdir(parents=True, exist_ok=True)
        
        # Import the generate_audio_with_elevenlabs function
        from src.platforms.workflow.integration import generate_audio_with_elevenlabs
        
        # Generate audio with ElevenLabs (this also cuts the audio as a side effect)
        loop = asyncio.get_event_loop()
        # output_dir for generate_audio_with_elevenlabs is where the main audio and parts/ subfolder go
        audio_file_path = await loop.run_in_executor(
            None,
            generate_audio_with_elevenlabs,
            heygen_script,
            audio_preview_base_dir, # Pass the base directory for previews
            title
        )

        if audio_file_path:
            # Store selected reel and original audio path in context.user_data
            context.user_data['selected_reel_for_heygen'] = selected_reel_metadata
            context.user_data['generated_audio_path'] = audio_file_path # Original full audio path
            
            # Construct and store the path to the directory containing cut audio parts
            audio_filename_base = Path(os.path.basename(audio_file_path)).stem
            parts_subdir_name = f"parts_{audio_filename_base}"
            cut_parts_dir_path = os.path.join(audio_preview_base_dir, parts_subdir_name)
            context.user_data['cut_parts_dir_path'] = cut_parts_dir_path
            logger.info(f"Stored cut parts directory for HeyGen: {cut_parts_dir_path}")
            
            # Create keyboard with confirmation buttons
            keyboard = [
                [InlineKeyboardButton("🚀 К генерации HeyGen видео (с аудиодорожками)", callback_data="heygen_proceed_audio_parts")],
                [InlineKeyboardButton("❌ Отмена", callback_data="heygen_cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send the original audio file to the user for preview
            try:
                with open(audio_file_path, 'rb') as audio_file_preview:
                    await context.bot.send_audio(
                        chat_id=query.message.chat_id,
                        audio=InputFile(audio_file_preview, filename=os.path.basename(audio_file_path)),
                        caption=f"🎙️ Аудио превью для '{title}' готово (нарезка аудио также выполнена). Прослушайте и подтвердите переход к генерации видео в HeyGen с использованием нарезанных аудиодорожек.",
                        title=title,
                        reply_markup=reply_markup # Attach keyboard to the audio message
                    )
                # Edit original message after sending audio
                await query.edit_message_text(f"Превью для '{title}' отправлено. Аудиодорожки для видео нарезаны. Выберите следующее действие.")
            except Exception as e:
                logger.error(f"Error sending audio file for reel '{title}': {e}")
                await query.edit_message_text(
                    f"⚠️ Ошибка при отправке аудио превью для '{title}'. Однако, аудио могло быть сгенерировано и нарезано. Выберите действие:",
                    reply_markup=reply_markup # Still show options
                )
        else:
            # Audio generation failed
            await query.edit_message_text(
                f"❌ Не удалось сгенерировать аудио для '{title}'. Пожалуйста, проверьте логи.",
                reply_markup=InlineKeyboardMarkup([[
                    # Corrected callback to go back to reel selection if possible, or main menu.
                    # Assuming menu_workflow or a similar state allows re-selection of Google Doc processing.
                    InlineKeyboardButton("Вернуться к выбору документа", callback_data="menu_workflow"), 
                    InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")
                ]])
            )

    except Exception as e:
        logger.error(f"Error in handle_reel_selection (audio generation/cutting part): {str(e)}\n{traceback.format_exc()}")
        await query.edit_message_text(
            f"❌ Произошла критическая ошибка при подготовке аудио: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")
            ]])
        )

async def handle_heygen_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user's confirmation to proceed with HeyGen video generation or cancel."""
    query = update.callback_query
    await query.answer()
    
    action = query.data # e.g., "heygen_proceed_audio_parts" or "heygen_cancel" or "upload_to_youtube" or "generate_another"
    selected_reel_metadata = context.user_data.get('selected_reel_for_heygen')
    generated_audio_path = context.user_data.get('generated_audio_path') # Original full audio
    cut_parts_dir_path = context.user_data.get('cut_parts_dir_path')
    generated_video_url = context.user_data.get('generated_video_url')
    reels = context.user_data.get('reels', [])
    generated_video_indices = context.user_data.get('generated_video_indices', [])

    if action == "heygen_proceed_audio_parts":
        if not selected_reel_metadata:
            await query.edit_message_text(
                "❌ Ошибка: данные о выбранном ролике не найдены. Пожалуйста, начните сначала.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")
                ]])
            )
            # Clean up keys if erroring out
            context.user_data.pop('selected_reel_for_heygen', None)
            context.user_data.pop('generated_audio_path', None)
            context.user_data.pop('cut_parts_dir_path', None)
            return
        if not cut_parts_dir_path or not os.path.isdir(cut_parts_dir_path):
            await query.edit_message_text(
                f"❌ Ошибка: директория с нарезанными аудиофайлами не найдена ({cut_parts_dir_path}). Пожалуйста, попробуйте выбрать ролик заново.",
                 reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back") # Or back to reel selection
                ]])
            )
            context.user_data.pop('selected_reel_for_heygen', None)
            context.user_data.pop('generated_audio_path', None)
            context.user_data.pop('cut_parts_dir_path', None)
            return

        title = selected_reel_metadata.get('title', 'Без названия')
        
        # Edit the caption of the audio message (where the button was clicked)
        # to remove buttons and show processing status.
        try:
            await query.edit_message_caption(
                caption=f"⏳ Отлично! Начинаю генерацию видео в HeyGen для ролика: {title} с использованием нарезанных аудиодорожек.\n\nЭто может занять несколько минут (до 10-15 мин)...",
                reply_markup=None # Remove buttons
            )
        except Exception as e:
            logger.error(f"Error editing audio message caption: {e}. Sending new status message.")
            # Fallback: send a new message if editing caption fails
            await query.message.reply_text(
                f"⏳ Отлично! Начинаю генерацию видео в HeyGen для ролика: {title} с использованием нарезанных аудиодорожек.\n\nЭто может занять несколько минут (до 10-15 мин)..."
            )

        import asyncio
        from src.platforms.workflow.integration import upload_to_drive, download_from_drive, upload_to_youtube
        from src.platforms.workflow.generate_heygen_video import upload_audio_file, generate_video_with_multiple_avatars, check_video_status
        
        # Get the event loop
        loop = asyncio.get_running_loop()
        
        # Get the HeyGen API key
        api_key = os.environ.get("HEYGEN_API_KEY", "NzYzODNmNTI5ODYyNGMyYTg1NzFhNTNmOWY4M2Q4OTYtMTc0MDczMjczOQ==")
        
        # Define avatar IDs
        avatar_1_id = "a7f27a8c3f954a54b599f04dff1ae4ac"
        avatar_2_id = "21095f74dfe9401a85d044c207d19f2b"
        
        # Find all the audio parts in the directory
        audio_paths = []
        if os.path.isdir(cut_parts_dir_path):
            audio_paths = sorted([
                os.path.join(cut_parts_dir_path, f) for f in os.listdir(cut_parts_dir_path)
                if f.startswith("part_") and f.endswith(".mp3")
            ], key=lambda x: int(os.path.basename(x).split("_")[1].split(".")[0]))
        
        if not audio_paths:
            await query.message.reply_text(f"❌ Ошибка: не найдены аудиофайлы в директории {cut_parts_dir_path}")
            return
        
        # Define avatars to use (alternating)
        avatar_ids = []
        for i in range(len(audio_paths)):
            avatar_ids.append(avatar_1_id if i % 2 == 0 else avatar_2_id)
        
        # Upload audio files and get asset IDs
        audio_asset_ids = []
        for audio_path in audio_paths:
            asset_id = await loop.run_in_executor(None, lambda: upload_audio_file(api_key, audio_path))
            if asset_id:
                audio_asset_ids.append(asset_id)
            else:
                await query.message.reply_text(f"❌ Ошибка при загрузке аудиофайла: {audio_path}")
                return
        
        # Generate video with the audio assets
        video_id = await loop.run_in_executor(
            None, 
            lambda: generate_video_with_multiple_avatars(api_key, avatar_ids, audio_asset_ids)
        )
        
        if not video_id:
            await query.message.reply_text("❌ Ошибка при генерации видео в HeyGen")
            return
        
        # Check video status until completed
        final_url = None
        status_message = await query.message.reply_text("⏳ Видео генерируется в HeyGen. Это может занять несколько минут...")
        
        # Poll for video status
        url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
        headers = {"X-Api-Key": api_key}
        
        max_retries = 60  # 10 min with 10s intervals
        for attempt in range(max_retries):
            try:
                response = await loop.run_in_executor(None, lambda: requests.get(url, headers=headers))
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("data", {}).get("status")
                    
                    if status == "completed":
                        final_url = result.get("data", {}).get("video_url")
                        await status_message.edit_text(f"✅ Видео успешно сгенерировано! URL: {final_url}")
                        break
                    elif status == "failed":
                        error = result.get("data", {}).get("error", "Unknown error")
                        await status_message.edit_text(f"❌ Ошибка при генерации видео: {error}")
                        return
                    elif status in ["processing", "pending", "waiting"]:
                        # Update status every few attempts to avoid too frequent message edits
                        if attempt % 5 == 0:
                            await status_message.edit_text(f"⏳ Статус видео: {status}. Проверка {attempt+1}/{max_retries}...")
                    else:
                        await status_message.edit_text(f"⚠️ Неизвестный статус: {status}")
                        return
                else:
                    await status_message.edit_text(f"❌ Ошибка при проверке статуса: {response.status_code}")
                    return
            except Exception as e:
                logger.error(f"Error checking video status: {e}")
            
            # Wait before next check
            await asyncio.sleep(10)
        
        # Store the URL for later use
        context.user_data['generated_video_url'] = final_url
        
        # Track which video was generated to avoid suggesting it again
        current_reel_idx = None
        for idx, reel in enumerate(reels):
            if reel['data'] == selected_reel_metadata:
                current_reel_idx = idx
                break
                
        if current_reel_idx is not None:
            if 'generated_video_indices' not in context.user_data:
                context.user_data['generated_video_indices'] = []
            context.user_data['generated_video_indices'].append(current_reel_idx)
        
        # Send the result as a NEW message
        result_message_text = ""
        if final_url:
            if "youtube.com" in final_url:
                result_message_text = (
                    f"✅ Видео для '{title}' успешно создано и загружено на YouTube!\\n\\n"
                    f"Ссылка: {final_url}"
                )
                # Add option to generate another video
                keyboard = [
                    [InlineKeyboardButton("🎬 Создать еще одно видео", callback_data="generate_another")],
                    [InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text(result_message_text, reply_markup=reply_markup)
            else: # HeyGen URL
                result_message_text = (
                    f"✅ Видео для '{title}' успешно создано в HeyGen! Вы можете загрузить его на YouTube.\\n\\n"
                    f"Ссылка на HeyGen видео: {final_url}"
                )
                # Show upload to YouTube option
                keyboard = [
                    [InlineKeyboardButton("📤 Загрузить на YouTube", callback_data="upload_to_youtube")],
                    [InlineKeyboardButton("🎬 Создать еще одно видео", callback_data="generate_another")],
                    [InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text(result_message_text, reply_markup=reply_markup)
        else:
            result_message_text = (
                f"❌ Произошла ошибка при генерации видео в HeyGen или загрузке на YouTube для '{title}'.\\n\\n"
                "Проверьте логи для получения дополнительной информации."
            )
            keyboard = [[InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(result_message_text, reply_markup=reply_markup)

        # Clean up audio files but keep metadata for other actions
        if generated_audio_path and os.path.exists(generated_audio_path): # remove original preview
            try:
                os.remove(generated_audio_path)
                logger.info(f"Cleaned up temporary original audio file: {generated_audio_path}")
            except OSError as e:
                logger.error(f"Error deleting temporary original audio file {generated_audio_path}: {e}")
        context.user_data.pop('generated_audio_path', None)
        context.user_data.pop('cut_parts_dir_path', None)

    elif action == "generate_another":
        # Show a list of available reels excluding the ones already generated
        reels = context.user_data.get('reels', [])
        generated_indices = context.user_data.get('generated_video_indices', [])
        
        # Filter out already generated reels
        available_reels = [(i, reel) for i, reel in enumerate(reels) if i not in generated_indices]
        
        if not available_reels:
            await query.edit_message_text(
                "Все доступные ролики уже были сгенерированы. Вы можете начать новый процесс.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")
                ]])
            )
            return
            
        # Create keyboard with remaining reels
        keyboard = []
        for i, reel in available_reels:
            title = reel['data'].get('title', f'Ролик {i+1}')
            # Limit title length to avoid button overflow
            if len(title) > 40:
                title = title[:37] + "..."
            keyboard.append([InlineKeyboardButton(f"{i+1}. {title}", callback_data=f"reel_{i}")])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Выберите следующий ролик для генерации видео:",
            reply_markup=reply_markup
        )

    elif action == "upload_to_youtube":
        # Get the stored video URL
        video_url = context.user_data.get('generated_video_url')
        if not video_url:
            await query.edit_message_text(
                "❌ Ошибка: ссылка на сгенерированное видео не найдена. Пожалуйста, сгенерируйте видео заново.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")
                ]])
            )
            return
            
        selected_reel_metadata = context.user_data.get('selected_reel_for_heygen')
        if not selected_reel_metadata:
            await query.edit_message_text(
                "❌ Ошибка: данные о ролике не найдены. Пожалуйста, начните процесс заново.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")
                ]])
            )
            return
            
        title = selected_reel_metadata.get('title', 'Без названия')
        
        # Update message to show upload progress
        await query.edit_message_text(f"⏳ Загружаю видео '{title}' на YouTube...")
        
        # Upload the video to YouTube
        import asyncio
        from src.platforms.workflow.integration import upload_to_drive, download_from_drive, upload_to_youtube
        
        # Get the event loop
        loop = asyncio.get_running_loop()
        
        # First upload to Drive
        drive_info = await loop.run_in_executor(
            None,
            lambda: upload_to_drive(video_url, f"{title.replace(' ', '_')[:30]}_video.mp4", title)
        )
        
        if not drive_info:
            await query.edit_message_text(
                f"❌ Ошибка: не удалось загрузить видео '{title}' на Google Drive.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")
                ]])
            )
            return
            
        # Get the file ID and download for YouTube upload
        file_id = drive_info.get('file_id')
        temp_video_path = drive_info.get('temp_path')
        
        try:
            # Ensure we have a valid temp path
            if not temp_video_path or not os.path.exists(temp_video_path):
                if file_id:
                    temp_video_path = await loop.run_in_executor(
                        None,
                        lambda: download_from_drive(file_id)
                    )
                else:
                    await query.edit_message_text(
                        f"❌ Ошибка: не удалось получить файл с Google Drive для загрузки на YouTube.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")
                        ]])
                    )
                    return
                    
            # Upload to YouTube
            description = selected_reel_metadata.get('description', '')
            tags = selected_reel_metadata.get('hashtags', [])
            
            video_id = await loop.run_in_executor(
                None,
                lambda: upload_to_youtube(temp_video_path, title, description, tags)
            )
            
            if video_id:
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                await query.edit_message_text(
                    f"✅ Видео '{title}' успешно загружено на YouTube!\n\nСсылка: {youtube_url}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🎬 Создать еще одно видео", callback_data="generate_another")],
                        [InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")]
                    ])
                )
            else:
                await query.edit_message_text(
                    f"❌ Ошибка: не удалось загрузить видео '{title}' на YouTube.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")
                    ]])
                )
        finally:
            # Clean up temporary file
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                    logger.info(f"Cleaned up temporary video file: {temp_video_path}")
                except OSError as e:
                    logger.error(f"Error deleting temporary video file {temp_video_path}: {e}")

    elif action == "heygen_cancel":
        try:
            await query.edit_message_caption(
                caption="Операция отменена. Аудиофайл удален. Вы можете выбрать другой ролик или вернуться в меню.",
                reply_markup=None # Remove buttons
            )
        except Exception as e:
            logger.error(f"Error editing audio message caption on cancel: {e}")
            await query.message.reply_text( # Fallback
                "Операция отменена. Аудиофайл удален. Вы можете выбрать другой ролик или вернуться в меню."
            )
       
        # Show menu button as a new message
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню 🏠", callback_data="menu_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Что делаем дальше?", reply_markup=reply_markup)

        # Clean up if cancelled
        context.user_data.pop('selected_reel_for_heygen', None)
        context.user_data.pop('generated_audio_path', None)
        context.user_data.pop('cut_parts_dir_path', None)
        if generated_audio_path and os.path.exists(generated_audio_path):
            try:
                os.remove(generated_audio_path)
                logger.info(f"Cleaned up temporary original audio file on cancel: {generated_audio_path}")
            except OSError as e:
                logger.error(f"Error deleting temporary original audio file {generated_audio_path} on cancel: {e}")
        if cut_parts_dir_path and os.path.isdir(cut_parts_dir_path):
             try:
                 import shutil
                 shutil.rmtree(cut_parts_dir_path)
                 logger.info(f"Cleaned up cut audio parts directory on cancel: {cut_parts_dir_path}")
             except OSError as e:
                 logger.error(f"Error deleting cut_parts_dir_path {cut_parts_dir_path} on cancel: {e}")

def main():
    """Start the bot."""
    logger.info("Starting bot...")
    
    # Create the Application
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    
    # Add high-priority command handlers first to ensure they work in any state
    application.add_handler(CommandHandler("start", start), group=0)
    application.add_handler(CommandHandler("restart", restart_command), group=0)
    application.add_handler(CommandHandler("help", help_command), group=0)
    application.add_handler(CommandHandler("menu", menu_command), group=0)
    application.add_handler(CommandHandler("sheet", sheet_command), group=0)
    application.add_handler(CommandHandler("logs", logs_command), group=0)
    
    # Create conversation handlers
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("menu", menu_command),
            CommandHandler("restart", restart_command),
            CallbackQueryHandler(handle_menu_selection, pattern="^menu_"),
            CallbackQueryHandler(handle_menu_selection, pattern="^workflow_multiple_reels$|^workflow_single_video$"),
            CallbackQueryHandler(menu_callback, pattern="^add_another_record$")
        ],
        states={
            WAITING_FOR_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url_input)
            ],
            WAITING_FOR_TRANSCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_transcription_input)
            ],
            WAITING_FOR_PLATFORM_SELECTION: [
                CallbackQueryHandler(handle_platform_selection, pattern="^platform_")
            ],
            WAITING_FOR_VECTOR_DB_QUERY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_vector_db_query)
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(filters.ALL, handle_unknown_input)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("menu", menu_command),
            CommandHandler("start", start),
            CommandHandler("restart", restart_command),
            CommandHandler("help", help_command),
            CallbackQueryHandler(handle_back_to_menu, pattern="^menu_back$|^back_to_menu$"),
            CommandHandler("sheet", sheet_command),
            MessageHandler(filters.ALL, unknown_text)
        ],
        name="main_conversation",
        persistent=False,
        conversation_timeout=300  # Timeout after 5 minutes of inactivity
    )
    
    # Add conversation handler
    application.add_handler(conv_handler)
    
    # Add callback handlers - note that these won't be reached if the conversation handler
    # is active, as it has higher priority
    application.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^menu_logs$|^menu_sheet$"))
    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^add_another_record$"))
    application.add_handler(CallbackQueryHandler(refresh_sheet_access_callback, pattern="^refresh_sheet_access$"))
    application.add_handler(CallbackQueryHandler(handle_menu_selection, pattern="^menu_update_sheet$|^menu_text_post$|^menu_vector_db$|^menu_workflow$|^menu_logs$|^menu_sheet$"))
    
    # Add handler for reel selection
    application.add_handler(CallbackQueryHandler(handle_reel_selection, pattern="^reel_\d+$"))
    
    # Add handler for HeyGen confirmation
    application.add_handler(CallbackQueryHandler(handle_heygen_confirmation, pattern="^(heygen_proceed_audio_parts|heygen_cancel|upload_to_youtube|generate_another)$"))
    
    # Add fallback handler for messages outside conversations
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))
    
    # Register the error handler
    application.add_error_handler(error_handler)
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main() 