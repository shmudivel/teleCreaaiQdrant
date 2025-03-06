from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
import os
from dotenv import load_dotenv
from crewai import Crew
from src.platforms.factory import PlatformFactory
from src.text_splitter import split_text_into_parts
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import re

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def extract_doc_id(url):
    """Extract Google Doc ID from URL."""
    patterns = [
        r'/document/d/([a-zA-Z0-9-_]+)',  # Standard Doc URL
        r'docs.google.com/document/d/([a-zA-Z0-9-_]+)',  # Shared Doc URL
        r'^([a-zA-Z0-9-_]+)$'  # Direct ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def read_from_google_doc(doc_id):
    """Read content from a Google Doc."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            './bustling-folio-439811-h8-539f8ab05fa7.json',
            scopes=['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
        )

        # Build the Docs API service
        docs_service = build('docs', 'v1', credentials=credentials)
        
        # Get the document content
        document = docs_service.documents().get(documentId=doc_id).execute()
        
        # Extract text from the document
        doc_content = ''
        for element in document.get('body').get('content'):
            if 'paragraph' in element:
                for para_element in element.get('paragraph').get('elements'):
                    if 'textRun' in para_element:
                        doc_content += para_element.get('textRun').get('content')
        
        return doc_content.strip()

    except Exception as e:
        logger.error(f"Error reading from Google Doc: {str(e)}")
        return None

def save_to_google_drive(text, comment, platform):
    try:
        credentials = service_account.Credentials.from_service_account_file(
            './bustling-folio-439811-h8-539f8ab05fa7.json',
            scopes=['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
        )

        drive_service = build('drive', 'v3', credentials=credentials)

        # Create or get the folder
        folder_name = "Social Media Responses"
        folders_result = drive_service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
            spaces='drive',
            fields='files(id, name)'
        ).execute()

        if not folders_result.get('files'):
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            folder_id = folder.get('id')
        else:
            folder_id = folders_result.get('files')[0].get('id')

        # Create a new document with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc_name = f"Response_{platform}_{timestamp}"
        
        file_metadata = {
            'name': doc_name,
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [folder_id]
        }

        file = drive_service.files().create(
            body=file_metadata,
            fields='id, name, webViewLink'
        ).execute()

        # Share the file
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': 'shmudivel@gmail.com'
        }

        drive_service.permissions().create(
            fileId=file['id'],
            body=permission,
            sendNotificationEmail=False
        ).execute()

        # Format the content
        content = f"""Generated Response:
{text}

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""

        # Update the document content using Docs API
        docs_service = build('docs', 'v1', credentials=credentials)
        docs_service.documents().batchUpdate(
            documentId=file['id'],
            body={
                'requests': [
                    {
                        'insertText': {
                            'location': {
                                'index': 1
                            },
                            'text': content
                        }
                    }
                ]
            }
        ).execute()

        return file.get('webViewLink')

    except Exception as e:
        logger.error(f"Error saving to Google Drive: {str(e)}")
        return None

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
    try:
        # Добавлена проверка наличиния сообщений
        if not context.user_data.get('messages') or len(context.user_data['messages']) < 1:
            await update.message.reply_text("❌ Ошибка: Нет сообщения для обработки")
            return

        source_content = context.user_data['messages'][0]
        platform = context.user_data.get('selected_platform', 'dzen')  # Default to dzen if not specified
        
        # Get platform-specific agents and tasks
        agents_class = PlatformFactory.get_platform_agents(platform)
        tasks_class = PlatformFactory.get_platform_tasks(platform)
        
        # Split text into 4 parts
        content_parts = split_text_into_parts(source_content, 4)
        
        # Create all four agents
        content_agent1 = agents_class.content_creator_agent()
        content_agent2 = agents_class.content_creator_agent_part2()
        content_agent3 = agents_class.content_creator_agent_part3()
        content_agent4 = agents_class.content_creator_agent_part4()
        
        # Create tasks for each part
        creation_task1 = tasks_class.content_creation_task(content_agent1, content_parts[0])
        creation_task2 = tasks_class.content_creation_task_part2(content_agent2, content_parts[1])
        creation_task3 = tasks_class.content_creation_task_part3(content_agent3, content_parts[2])
        creation_task4 = tasks_class.content_creation_task_part4(content_agent4, content_parts[3])
        
        # Set up the crew with all agents and tasks
        crew = Crew(
            agents=[content_agent1, content_agent2, content_agent3, content_agent4],
            tasks=[creation_task1, creation_task2, creation_task3, creation_task4]
        )
        
        msg_to_edit = message if message else update.message
        await msg_to_edit.reply_text("Начинаю обработку контента (это может занять некоторое время)...")
        
        # Run all tasks
        result = crew.kickoff()
        
        # Combine all results
        combined_output = f"""
--- Part 1 ---
{creation_task1.output}

--- Part 2 ---
{creation_task2.output}

--- Part 3 ---
{creation_task3.output}

--- Part 4 ---
{creation_task4.output}
"""
        
        # Create literary editor agent
        literary_editor = agents_class.literary_editor_agent()
        
        # Create literary editing task
        literary_editing_task = tasks_class.literary_editing_task(literary_editor, combined_output)
        
        # Create final editor agent
        final_editor = agents_class.final_editor_agent()

        # Create SEO optimizer agent
        seo_optimizer = agents_class.seo_optimizer_agent()
        
        # Create tasks for SEO and final editing
        seo_task = tasks_class.seo_optimization_task(seo_optimizer, combined_output)
        
        # Add literary editing step to the workflow
        await msg_to_edit.reply_text("Улучшаю литературный стиль текста...")
        
        # Run literary editing
        literary_crew = Crew(
            agents=[literary_editor],
            tasks=[literary_editing_task]
        )
        literary_result = literary_crew.kickoff()
        
        # Use the literary edited content for final editing
        final_editing_task = tasks_class.final_editing_task(final_editor, literary_editing_task.output)
        
        # Final crew with SEO and final editor
        final_crew = Crew(
            agents=[seo_optimizer, final_editor],
            tasks=[seo_task, final_editing_task]
        )

        await msg_to_edit.reply_text("Выполняю финальную редакцию поста...")

        # Run final editing
        final_result = final_crew.kickoff()

        # Get platform display name for the document
        platforms = PlatformFactory.get_available_platforms()
        platform_name = platforms.get(platform, platform)

        # Use the final edited result for saving
        post_link = save_to_google_drive(
            final_editing_task.output, 
            source_content, 
            platform_name
        )
        
        # Send the result
        await msg_to_edit.reply_text(f"✅ Пост для {platform_name} готов!")
        
        if post_link:
            await msg_to_edit.reply_text(f"Ссылка на пост: {post_link}")
        
        context.user_data['messages'] = []
        
    except Exception as e:
        logger.error(f"Error processing content: {str(e)}")
        msg_to_edit = message if message else update.message
        await msg_to_edit.reply_text(f"Произошла ошибка при обработке контента: {str(e)}")
        context.user_data['messages'] = []

def main():
    """Start the bot."""
    # Load environment variables
    load_dotenv()
    
    # Create the Application
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add callback query handler for platform selection
    application.add_handler(CallbackQueryHandler(handle_platform_selection, pattern=r'^platform_'))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    main() 