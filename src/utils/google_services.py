import re
import logging
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configure logging
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
    """Save content to Google Drive and return the link."""
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