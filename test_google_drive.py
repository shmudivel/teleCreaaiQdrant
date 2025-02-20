import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

def test_google_drive_access():
    # Use the JSON file directly
    credentials = service_account.Credentials.from_service_account_file(
        '/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/bustling-folio-439811-h8-539f8ab05fa7.json',
        scopes=['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
    )

    try:
        # Build the Drive API service
        drive_service = build('drive', 'v3', credentials=credentials)

        # Create a folder if it doesn't exist
        folder_name = "Test Bot Files"
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
            'name': 'Test Document',
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [folder_id]  # This puts the file in the folder
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

        # Also share the folder
        drive_service.permissions().create(
            fileId=folder_id,
            body=permission,
            sendNotificationEmail=False
        ).execute()

        print(f"\nCreated and shared file: {file['name']}")
        print(f"File ID: {file['id']}")
        print(f"Web View Link: {file.get('webViewLink', 'Link not available')}")
        print(f"Located in folder: {folder_name}")
        print(f"Shared with: shmudivel@gmail.com")

        # List files in the folder
        print(f"\nListing files in '{folder_name}':")
        results = drive_service.files().list(
            q=f"'{folder_id}' in parents",
            pageSize=10,
            fields="files(id, name, webViewLink, mimeType)"
        ).execute()
        
        files = results.get('files', [])

        if not files:
            print('No files found in folder.')
        else:
            for file in files:
                file_type = "📄 Doc" if file['mimeType'] == 'application/vnd.google-apps.document' else "📁 Folder"
                print(f"- {file_type} | {file['name']} ({file['id']})")
                print(f"  Link: {file.get('webViewLink', 'Link not available')}")

        print("\nGoogle Drive access test successful!")
        return True

    except Exception as e:
        print(f"Error accessing Google Drive: {str(e)}")
        return False

if __name__ == "__main__":
    test_google_drive_access()