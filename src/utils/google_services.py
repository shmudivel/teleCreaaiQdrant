import re
import logging
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import time

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

def ensure_sheet_accessible(spreadsheet_id):
    """
    Ensure the spreadsheet is accessible by trying multiple sharing methods.
    This is a fallback function if normal permission sharing fails.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
        
    Returns:
        Dictionary with success status and sharing information
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            './bustling-folio-439811-h8-539f8ab05fa7.json',
            scopes=['https://www.googleapis.com/auth/drive']
        )
        
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # List current permissions
        permissions = drive_service.permissions().list(
            fileId=spreadsheet_id,
            fields='permissions(id,emailAddress,role,type)'
        ).execute()
        
        logger.info(f"Current permissions: {permissions}")
        
        # Try different sharing methods
        sharing_methods = [
            # Method 1: Share with specific email
            {
                'type': 'user',
                'role': 'writer',
                'emailAddress': 'shmudivel@gmail.com'
            },
            # Method 2: Share with domain
            {
                'type': 'domain',
                'role': 'writer',
                'domain': 'gmail.com'
            },
            # Method 3: Anyone with the link can edit
            {
                'type': 'anyone',
                'role': 'writer',
                'allowFileDiscovery': False
            },
            # Method 4: Anyone with the link can view (public sharing)
            {
                'type': 'anyone',
                'role': 'reader',
                'allowFileDiscovery': False
            }
        ]
        
        results = []
        sharing_links = {}
        
        for i, method in enumerate(sharing_methods):
            try:
                logger.info(f"Trying sharing method {i+1}: {method}")
                
                response = drive_service.permissions().create(
                    fileId=spreadsheet_id,
                    body=method,
                    fields='id,type,role',
                    sendNotificationEmail=False  # Don't send notification emails
                ).execute()
                
                logger.info(f"Method {i+1} success: {response}")
                results.append({
                    'method': i+1,
                    'success': True,
                    'details': {
                        **response,
                        'type': method.get('type'),
                        'role': method.get('role'),
                        'email': method.get('emailAddress', None),
                        'domain': method.get('domain', None)
                    }
                })
                
                # If this is one of the "anyone with link" methods, get the sharing link
                if method['type'] == 'anyone':
                    # Update to make the document accessible
                    drive_service.files().update(
                        fileId=spreadsheet_id,
                        body={
                            'copyRequiresWriterPermission': False
                        }
                    ).execute()
                    
                    # Get the shareable link
                    file = drive_service.files().get(
                        fileId=spreadsheet_id, 
                        fields='webViewLink'
                    ).execute()
                    
                    link_type = 'edit_link' if method['role'] == 'writer' else 'view_link'
                    sharing_links[link_type] = file.get('webViewLink', f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
                    logger.info(f"Created {link_type}: {sharing_links[link_type]}")
                
            except Exception as e:
                logger.warning(f"Method {i+1} failed: {str(e)}")
                results.append({
                    'method': i+1,
                    'success': False,
                    'error': str(e),
                    'details': {
                        'type': method.get('type'),
                        'role': method.get('role')
                    }
                })
        
        # After all methods, get the updated permissions
        updated_permissions = drive_service.permissions().list(
            fileId=spreadsheet_id,
            fields='permissions(id,emailAddress,role,type)'
        ).execute()
        
        logger.info(f"Updated permissions: {updated_permissions}")
        
        # Generate direct links
        sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        
        # Create the return object
        return {
            'success': any(result['success'] for result in results),
            'results': results,
            'permissions': updated_permissions.get('permissions', []),
            'spreadsheet_id': spreadsheet_id,
            'sheet_url': sheet_url,
            'sharing_links': sharing_links
        }
        
    except Exception as e:
        logger.error(f"Error ensuring sheet accessibility: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def save_telegram_message_to_sheet(user_id, text, url=None):
    """
    Save Telegram message data to a Google Sheet.
    
    Args:
        user_id: Telegram user ID
        text: Message text
        url: URL (optional)
        
    Returns:
        Dictionary with success status, spreadsheet_id and sheet_url if successful
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            './bustling-folio-439811-h8-539f8ab05fa7.json',
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        
        # Build the Sheets and Drive API services
        sheets_service = build('sheets', 'v4', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # Find spreadsheet by name, or create a new one
        spreadsheet_name = "Telegram Messages"
        spreadsheet_id = None
        web_view_link = None
        is_new_sheet = False
        
        # Try to find the spreadsheet
        results = drive_service.files().list(
            q=f"name='{spreadsheet_name}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
            spaces='drive',
            fields='files(id, name, webViewLink)'
        ).execute()
        
        items = results.get('files', [])
        
        if items:
            # Use existing spreadsheet
            spreadsheet_id = items[0]['id']
            web_view_link = items[0].get('webViewLink', f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
            logger.info(f"Found existing spreadsheet: {spreadsheet_id}")
            
            try:
                # Check if sheet "Messages" exists
                sheets_service.spreadsheets().get(
                    spreadsheetId=spreadsheet_id,
                    ranges=['Messages!A1'],
                    includeGridData=False
                ).execute()
                
                logger.info("Sheet 'Messages' exists")
            except Exception as e:
                logger.warning(f"Sheet 'Messages' may not exist, creating it: {str(e)}")
                
                # Create new "Messages" sheet
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={
                        'requests': [
                            {
                                'addSheet': {
                                    'properties': {
                                        'title': 'Messages'
                                    }
                                }
                            }
                        ]
                    }
                ).execute()
                
                # Add headers
                sheets_service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range='Messages!A1',
                    valueInputOption='RAW',
                    body={
                        'values': [
                            ['Timestamp', 'User ID', 'Text', 'URL']
                        ]
                    }
                ).execute()
                
                logger.info("Created new 'Messages' sheet with headers")
        else:
            # Create new spreadsheet
            spreadsheet = sheets_service.spreadsheets().create(
                body={
                    'properties': {
                        'title': spreadsheet_name
                    },
                    'sheets': [
                        {
                            'properties': {
                                'title': 'Messages'
                            }
                        }
                    ]
                }
            ).execute()
            
            spreadsheet_id = spreadsheet['spreadsheetId']
            is_new_sheet = True
            logger.info(f"Created new spreadsheet: {spreadsheet_id}")
            
            # Add headers
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Messages!A1',
                valueInputOption='RAW',
                body={
                    'values': [
                        ['Timestamp', 'User ID', 'Text', 'URL']
                    ]
                }
            ).execute()
            
            # Get the web view link
            file = drive_service.files().get(
                fileId=spreadsheet_id,
                fields='webViewLink'
            ).execute()
            
            web_view_link = file.get('webViewLink', f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
            logger.info(f"New spreadsheet web view link: {web_view_link}")
            
            # Wait for the spreadsheet to be fully created
            time.sleep(1)
        
        # Get the next empty row
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='Messages!A:A'
        ).execute()
        
        values = result.get('values', [])
        next_row = len(values) + 1
        
        # Add the new row
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        range_name = f'Messages!A{next_row}'
        
        # Limit text size to avoid errors (maximum 10000 characters)
        text_to_add = text
        if len(text_to_add) > 10000:
            text_to_add = text_to_add[:9997] + "..."
            
        body = {
            'values': [
                [timestamp, str(user_id), text_to_add, url or '']
            ]
        }
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        logger.info(f"Added new message record in row {next_row}")
        
        # Always ensure the sheet is accessible after creating or updating
        ensure_results = ensure_sheet_accessible(spreadsheet_id)
        logger.info(f"Ensure sheet accessible results: {ensure_results}")
        
        # Extract sharing links if available
        sharing_links = ensure_results.get('sharing_links', {})
        view_link = sharing_links.get('view_link', web_view_link)
        edit_link = sharing_links.get('edit_link', web_view_link)
        
        # Return success with additional info
        return {
            'success': True,
            'spreadsheet_id': spreadsheet_id,
            'sheet_url': web_view_link,
            'view_link': view_link,
            'edit_link': edit_link,
            'is_new_sheet': is_new_sheet,
            'ensure_results': ensure_results
        }
        
    except Exception as e:
        logger.error(f"Error saving Telegram message to sheet: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_telegram_messages(limit=50, user_id=None):
    """
    Retrieve message records from the Telegram Messages spreadsheet.
    
    Args:
        limit: Maximum number of records to retrieve (default 50)
        user_id: Filter by specific user ID (optional)
        
    Returns:
        List of message records or None on error
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            './bustling-folio-439811-h8-539f8ab05fa7.json',
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # Build the Sheets API service
        sheets_service = build('sheets', 'v4', credentials=credentials)
        
        # Find the spreadsheet
        drive_service = build('drive', 'v3', credentials=credentials)
        spreadsheet_name = "Telegram Messages"
        
        files_result = drive_service.files().list(
            q=f"name='{spreadsheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        if not files_result.get('files'):
            logger.warning(f"Spreadsheet '{spreadsheet_name}' not found")
            return None
        
        spreadsheet_id = files_result.get('files')[0].get('id')
        
        # Get all records
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='Messages!A:D'
        ).execute()
        
        values = result.get('values', [])
        
        if len(values) <= 1:  # Only header or empty
            return []
        
        # Convert to list of dictionaries
        header = values[0]
        records = []
        
        # Skip header row and process records
        for i, row in enumerate(values[1:limit+1]):
            # Pad row with empty strings if needed
            padded_row = row + [''] * (len(header) - len(row))
            
            record = dict(zip(header, padded_row))
            
            # Filter by user_id if specified
            if user_id and record.get('Telegram ID') != str(user_id):
                continue
                
            records.append(record)
        
        return records
        
    except Exception as e:
        logger.error(f"Error retrieving Telegram messages: {str(e)}")
        return None

def get_telegram_sheet_url():
    """
    Get detailed information about the Telegram Messages spreadsheet.
    
    Returns:
        Dictionary with URLs and metadata
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            './bustling-folio-439811-h8-539f8ab05fa7.json',
            scopes=['https://www.googleapis.com/auth/drive']
        )
        
        # Find the spreadsheet
        drive_service = build('drive', 'v3', credentials=credentials)
        spreadsheet_name = "Telegram Messages"
        
        files_result = drive_service.files().list(
            q=f"name='{spreadsheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'",
            spaces='drive',
            fields='files(id, name, webViewLink, owners, permissions, createdTime, modifiedTime)'
        ).execute()
        
        if not files_result.get('files'):
            logger.warning(f"Spreadsheet '{spreadsheet_name}' not found")
            return {
                'success': False,
                'error': f"Spreadsheet '{spreadsheet_name}' not found"
            }
        
        # Get detailed information
        spreadsheet = files_result.get('files')[0]
        spreadsheet_id = spreadsheet.get('id')
        web_view_link = spreadsheet.get('webViewLink', f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        created_time = spreadsheet.get('createdTime', 'Unknown')
        modified_time = spreadsheet.get('modifiedTime', 'Unknown')
        
        # Get ownership and permission info
        owners_info = spreadsheet.get('owners', [])
        permissions_info = spreadsheet.get('permissions', [])
        
        owner_emails = [owner.get('emailAddress', 'unknown') for owner in owners_info] if owners_info else ['Unknown']
        shared_emails = []
        
        for perm in permissions_info:
            if perm.get('type') == 'user' and perm.get('emailAddress') != owner_emails[0]:
                shared_emails.append({
                    'email': perm.get('emailAddress', 'unknown'),
                    'role': perm.get('role', 'unknown')
                })
        
        # Get the sheets list and row counts
        try:
            sheets_service = build('sheets', 'v4', credentials=credentials)
            sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = sheet_metadata.get('sheets', [])
            
            sheets_info = []
            for sheet in sheets:
                sheet_title = sheet.get('properties', {}).get('title', 'Unknown')
                sheet_id = sheet.get('properties', {}).get('sheetId', 'Unknown')
                
                # Get row count
                try:
                    range_name = f"{sheet_title}!A:A"
                    result = sheets_service.spreadsheets().values().get(
                        spreadsheetId=spreadsheet_id,
                        range=range_name
                    ).execute()
                    rows = len(result.get('values', []))
                except:
                    rows = 'Unknown'
                
                sheets_info.append({
                    'title': sheet_title,
                    'id': sheet_id,
                    'rows': rows
                })
        except Exception as e:
            logger.error(f"Error getting sheet details: {str(e)}")
            sheets_info = []
        
        return {
            'success': True,
            'spreadsheet_id': spreadsheet_id,
            'name': spreadsheet_name,
            'url': web_view_link,
            'created': created_time,
            'modified': modified_time,
            'owner': owner_emails[0],
            'shared_with': shared_emails,
            'sheets': sheets_info,
            'drive_url': "https://drive.google.com/drive/search?q=type:spreadsheet%20name:%22Telegram%20Messages%22"
        }
        
    except Exception as e:
        logger.error(f"Error getting Telegram sheet URL: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        } 