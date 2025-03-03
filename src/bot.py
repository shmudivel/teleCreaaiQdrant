from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os
from dotenv import load_dotenv
from crewai import Crew
from .tasks import SocialMediaTask
from .agents import SocialMediaAgent
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
        'Здравствуйте! Я помогу вам создавать информативные комментарии для соцсетей.\n\n'
        'Чтобы начать, отправьте мне:\n'
        '1. Ссылку на Google Doc с комментарием\n'
        'Команда /help - если нужна помощь\n\n'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        'Как я работаю:\n'
        '/start - Начать работу\n'
        '/help - Показать это сообщение\n\n'
        'Отправьте ссылку на Google Doc с комментарием и укажите соцсеть - я помогу составить информативный ответ'
    )

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
        await update.message.reply_text(
            "Отлично! Сейчас создам адаптированный пост из 4 частей... ✍️"
        )
        
        try:
            source_content = context.user_data['messages'][0]
            
            # Split text into 4 parts
            from src.text_splitter import split_text_into_parts
            content_parts = split_text_into_parts(source_content, 4)
            
            tasks = SocialMediaTask()
            agents = SocialMediaAgent()
            
            # Create all four agents
            content_agent1 = agents.content_creator_agent()
            content_agent2 = agents.content_creator_agent_part2()
            content_agent3 = agents.content_creator_agent_part3()
            content_agent4 = agents.content_creator_agent_part4()
            
            # Create tasks for each part
            creation_task1 = tasks.content_creation_task(content_agent1, content_parts[0])
            creation_task2 = tasks.content_creation_task_part2(content_agent2, content_parts[1])
            creation_task3 = tasks.content_creation_task_part3(content_agent3, content_parts[2])
            creation_task4 = tasks.content_creation_task_part4(content_agent4, content_parts[3])
            
            # Set up the crew with all agents and tasks
            crew = Crew(
                agents=[content_agent1, content_agent2, content_agent3, content_agent4],
                tasks=[creation_task1, creation_task2, creation_task3, creation_task4]
            )
            
            await update.message.reply_text("Начинаю обработку контента (это может занять некоторое время)...")
            
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
            
            # Create final editor agent
            final_editor = agents.final_editor_agent()

            # Create final editing task with combined content
            final_editing_task = tasks.final_editing_task(final_editor, combined_output)

            # После объединения контента и перед финальной редакцией
            seo_optimizer = agents.seo_optimizer_agent()
            seo_task = tasks.seo_optimization_task(seo_optimizer, combined_output)
            
            # Добавляем SEO-агента в crew
            final_crew = Crew(
                agents=[seo_optimizer, final_editor],
                tasks=[seo_task, final_editing_task]
            )

            await update.message.reply_text("Выполняю финальную редакцию поста...")

            # Run final editing
            final_result = final_crew.kickoff()

            # Use the final edited result for saving
            post_link = save_to_google_drive(
                final_editing_task.output, 
                source_content, 
                "Соцсети"
            )
            
            # Send the result
            await update.message.reply_text("✅ Пост из 4 частей готов!")
            
            if post_link:
                await update.message.reply_text(f"Ссылка на пост: {post_link}")
            
            context.user_data['messages'] = []
            
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            await update.message.reply_text(
                "Упс! Что-то пошло не так 😅 Давайте попробуем еще раз?"
            )
            context.user_data['messages'] = []

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