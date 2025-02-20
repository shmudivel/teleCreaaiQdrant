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

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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