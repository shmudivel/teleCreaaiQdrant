from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os
from dotenv import load_dotenv
from crewai import Crew
from .tasks import contentSocialMediaTasks
from .agents import contentSocialMediaAgents
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
        content = f"""Original Comment ({platform}):
{comment}

Generated Response:
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
                "Пожалуйста, отправьте корректную ссылку на Google Doc 📄"
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
            "Отлично! Теперь укажите, из какой соцсети комментарий (например: ВКонтакте, Telegram, Дзен) 🌐"
        )
    else:
        context.user_data['messages'].append(current_message)
        
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
            final_text = str(result)
            
            # Save to Google Drive and get the link
            doc_link = save_to_google_drive(final_text, original_comment, social_platform)
            
            # Send the response and document link to Telegram
            await update.message.reply_text(final_text)
            if doc_link:
                await update.message.reply_text(
                    f"Ответ сохранен в Google Docs: {doc_link}"
                )
            
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