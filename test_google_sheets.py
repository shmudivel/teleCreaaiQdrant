import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

def test_google_sheets_or_docs():
    """
    Test function to connect to Google Sheets (if API enabled) or 
    fallback to Google Docs/Drive (which is confirmed working).
    """
    # Load credentials from the service account file
    credentials = service_account.Credentials.from_service_account_file(
        'bustling-folio-439811-h8-539f8ab05fa7.json',
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file'
        ]
    )

    try:
        # First attempt to use Sheets API
        print("Attempting to use Google Sheets API...")
        try:
            # Build the Sheets API service
            sheets_service = build('sheets', 'v4', credentials=credentials)
            
            # Create a new spreadsheet
            spreadsheet_body = {
                'properties': {
                    'title': 'Test Spreadsheet'
                }
            }
            
            spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
            spreadsheet_id = spreadsheet['spreadsheetId']
            
            print(f"Created new spreadsheet with ID: {spreadsheet_id}")
            print(f"Spreadsheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
            
            # Add data to the spreadsheet
            range_name = 'Sheet1!A1:D5'
            values = [
                ['Name', 'Email', 'Phone', 'Date'],
                ['John Doe', 'john@example.com', '555-1234', '2023-05-01'],
                ['Jane Smith', 'jane@example.com', '555-5678', '2023-05-02'],
                ['Bob Johnson', 'bob@example.com', '555-9012', '2023-05-03']
            ]
            
            body = {
                'values': values
            }
            
            result = sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"{result.get('updatedCells')} cells updated.")
            print("Google Sheets connection test successful!")
            
            # Share the spreadsheet with a specific email
            drive_service = build('drive', 'v3', credentials=credentials)
            
            permission = {
                'type': 'user',
                'role': 'writer',
                'emailAddress': 'shmudivel@gmail.com'
            }
            
            drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission,
                sendNotificationEmail=False
            ).execute()
            
            print(f"Spreadsheet shared with: {permission['emailAddress']}")
            return True
            
        except Exception as sheets_error:
            print(f"Error with Google Sheets API: {str(sheets_error)}")
            print("Falling back to Google Drive API for document creation...")
            
            # Build the Drive API service
            drive_service = build('drive', 'v3', credentials=credentials)
            
            # Create a folder if it doesn't exist
            folder_name = "Test Data Records"
            folders_result = drive_service.files().list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            if not folders_result.get('files'):
                # Create new folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = drive_service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                folder_id = folder.get('id')
                print(f"Created new folder: {folder_name}")
            else:
                folder_id = folders_result.get('files')[0].get('id')
                print(f"Using existing folder: {folder_name}")
            
            # Create a new Google Doc in the folder
            file_metadata = {
                'name': 'Test Data Record',
                'mimeType': 'application/vnd.google-apps.document',
                'parents': [folder_id]
            }
            
            file = drive_service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink'
            ).execute()
            
            # Share the file with specific email
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
            
            print(f"\nCreated and shared file: {file['name']}")
            print(f"File ID: {file['id']}")
            print(f"Web View Link: {file.get('webViewLink', 'Link not available')}")
            print(f"Located in folder: {folder_name}")
            print(f"Shared with: shmudivel@gmail.com")
            print("Google Drive document creation successful!")
            return True
            
    except Exception as e:
        print(f"Error connecting to Google services: {str(e)}")
        return False

if __name__ == "__main__":
    test_google_sheets_or_docs() 