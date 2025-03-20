from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler, ConversationHandler
import os
from dotenv import load_dotenv
from crewai import Crew
import logging
import asyncio
import sys
import traceback
import html

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
    WAITING_FOR_PLATFORM_SELECTION
) = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
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
    
    return ConversationHandler.END

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the main menu with available options."""
    keyboard = [
        [InlineKeyboardButton("Создать текстовый пост 📝", callback_data="menu_text_post")],
        [InlineKeyboardButton("Обновить Google Sheet 📊", callback_data="menu_update_sheet")]
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
        '/help - Показать эту справку\n\n'
        'В главном меню доступны следующие опции:\n'
        '• Создать текстовый пост - создать пост для выбранной соцсети (Дзен, VC.ru)\n'
        '• Обновить Google Sheet - добавить запись в таблицу сообщений\n\n'
        'Для админов доступны дополнительные команды:\n'
        '/logs [число] - Показать последние записи из логов\n'
        '/sheet - Получить ссылку на Google Sheet с логами'
    )
    
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
        
        # Create inline keyboard for main menu
        keyboard = [
            [InlineKeyboardButton("Создать текстовый пост 📝", callback_data="menu_text_post")],
            [InlineKeyboardButton("Обновить Google Sheet 📊", callback_data="menu_update_sheet")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send new message with main menu options
        try:
            await query.message.reply_text(
                "Выберите действие:",
                reply_markup=reply_markup
            )
            logger.info(f"Successfully sent main menu to user {user_id}")
        except Exception as reply_error:
            logger.error(f"Error sending main menu: {str(reply_error)}")
            await query.message.reply_text("Используйте /start для возврата в главное меню.")
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error returning to menu: {str(e)}")
        try:
            await query.message.reply_text("Используйте /start для возврата в главное меню.")
        except:
            logger.error("Failed to send fallback message")
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
        response = f"📊 Последние {len(logs)} записей из логов:\n\n"
        
        for i, log in enumerate(logs):
            # Get first 30 chars of text
            text_preview = log.get('Text', '')[:30] + ('...' if len(log.get('Text', '')) > 30 else '')
            
            response += f"{i+1}. User: {log.get('Telegram ID')}\n"
            response += f"   Time: {log.get('Date and Time')}\n"
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

def main():
    """Start the bot."""
    logger.info("Starting bot...")
    
    # Create the Application
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    
    # Create conversation handlers
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("menu", menu_command),
            CallbackQueryHandler(handle_menu_selection, pattern="^menu_"),
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
            ConversationHandler.TIMEOUT: [
                MessageHandler(filters.ALL, handle_unknown_input)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("menu", menu_command),
            CommandHandler("start", start),
            CommandHandler("help", help_command),
            CallbackQueryHandler(handle_back_to_menu, pattern="^menu_back$"),
            MessageHandler(filters.ALL, unknown_text)
        ],
        name="main_conversation",
        persistent=False,
        conversation_timeout=300  # Timeout after 5 minutes of inactivity
    )
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("sheet", sheet_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("logs", logs_command))
    
    # Add conversation handler
    application.add_handler(conv_handler)
    
    # Add callback handlers - note that these won't be reached if the conversation handler
    # is active, as it has higher priority
    application.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^menu_logs$|^menu_sheet$"))
    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^add_another_record$"))
    application.add_handler(CallbackQueryHandler(refresh_sheet_access_callback, pattern="^refresh_sheet_access$"))
    
    # Add fallback handler for messages outside conversations
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))
    
    # Register the error handler
    application.add_error_handler(error_handler)
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main() 