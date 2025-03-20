import os
import json
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

def create_table_in_google_doc():
    """
    Create a document with tabular data in Google Docs as an alternative to Google Sheets.
    This is a workaround until the Google Sheets API is enabled for this project.
    """
    # Load credentials from the service account file
    credentials = service_account.Credentials.from_service_account_file(
        'bustling-folio-439811-h8-539f8ab05fa7.json',
        scopes=[
            'https://www.googleapis.com/auth/documents',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file'
        ]
    )

    try:
        # Build the Drive API service
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # Build the Docs API service
        docs_service = build('docs', 'v1', credentials=credentials)
        
        # Create a folder if it doesn't exist
        folder_name = "Data Records"
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
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        file_metadata = {
            'name': f'Data Records - {current_time}',
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [folder_id]
        }
        
        doc = drive_service.files().create(
            body=file_metadata,
            fields='id, name, webViewLink'
        ).execute()
        
        document_id = doc['id']
        
        # Create a table in the document
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1
                    },
                    'text': 'Data Records\n\n'
                }
            },
            {
                'insertTable': {
                    'rows': 5,
                    'columns': 4,
                    'location': {
                        'index': 15  # After the title and newlines
                    }
                }
            }
        ]
        
        docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()
        
        # Get the document to find the table location
        document = docs_service.documents().get(documentId=document_id).execute()
        
        # Find the table and its cells
        table_cells = []
        table_start_index = None
        
        for element in document.get('body').get('content'):
            if 'table' in element:
                table = element.get('table')
                table_start_index = element.get('startIndex')
                
                for row in table.get('tableRows'):
                    for cell in row.get('tableCells'):
                        cell_location = cell.get('startIndex')
                        table_cells.append(cell_location)
        
        if table_cells:
            # Insert data into the table cells
            data = [
                ["Name", "Email", "Phone", "Date"],
                ["John Doe", "john@example.com", "555-1234", "2023-05-01"],
                ["Jane Smith", "jane@example.com", "555-5678", "2023-05-02"],
                ["Bob Johnson", "bob@example.com", "555-9012", "2023-05-03"],
                ["Alice Brown", "alice@example.com", "555-3456", "2023-05-04"]
            ]
            
            data_requests = []
            
            # Iterate through cells and insert data
            cell_index = 0
            for row_idx, row in enumerate(data):
                for col_idx, cell_data in enumerate(row):
                    if cell_index < len(table_cells):
                        data_requests.append({
                            'insertText': {
                                'location': {
                                    'index': table_cells[cell_index] + 1  # +1 to get inside the cell
                                },
                                'text': cell_data
                            }
                        })
                        cell_index += 1
            
            # Format header row (make bold)
            if table_start_index is not None:
                header_range = {
                    'startIndex': table_cells[0],
                    'endIndex': table_cells[3] + len(data[0][3]) + 1  # End of the last header cell
                }
                
                data_requests.append({
                    'updateTextStyle': {
                        'range': header_range,
                        'textStyle': {
                            'bold': True
                        },
                        'fields': 'bold'
                    }
                })
            
            # Apply the changes
            docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': data_requests}
            ).execute()
        
        # Share the document with a specific email
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': 'shmudivel@gmail.com'  # Replace with the email you want to share with
        }
        
        drive_service.permissions().create(
            fileId=document_id,
            body=permission,
            sendNotificationEmail=False
        ).execute()
        
        print(f"\nCreated and shared document: {doc['name']}")
        print(f"Document ID: {document_id}")
        print(f"Web View Link: {doc.get('webViewLink', 'Link not available')}")
        print(f"Located in folder: {folder_name}")
        print(f"Shared with: {permission['emailAddress']}")
        print("Document creation successful!")
        
        return {
            'success': True,
            'document_id': document_id,
            'link': doc.get('webViewLink')
        }
        
    except Exception as e:
        print(f"Error creating Google Docs table: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def add_record_to_doc(document_id, record_data):
    """
    Add a new record (row) to an existing Google Doc with a table.
    
    Args:
        document_id: The ID of the Google Doc
        record_data: List of values to add as a new row
    """
    # Load credentials from the service account file
    credentials = service_account.Credentials.from_service_account_file(
        'bustling-folio-439811-h8-539f8ab05fa7.json',
        scopes=['https://www.googleapis.com/auth/documents']
    )
    
    try:
        # Build the Docs API service
        docs_service = build('docs', 'v1', credentials=credentials)
        
        # Get the document to find the table
        document = docs_service.documents().get(documentId=document_id).execute()
        
        # Find the table and its dimensions
        table = None
        table_index = None
        
        for i, element in enumerate(document.get('body').get('content')):
            if 'table' in element:
                table = element.get('table')
                table_index = i
                break
        
        if table:
            # Get the number of rows in the table
            num_rows = len(table.get('tableRows', []))
            
            # Append a new row to the table
            # Use rowIndex = num_rows - 1 to insert after the last row
            requests = [
                {
                    'insertTableRow': {
                        'tableCellLocation': {
                            'tableStartLocation': {
                                'index': document.get('body').get('content')[table_index].get('startIndex')
                            },
                            'rowIndex': num_rows - 1,  # Last row index (0-based)
                            'columnIndex': 0
                        },
                        'insertBelow': True
                    }
                }
            ]
            
            # Insert the new row
            docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            # Get updated document to find the new cells
            updated_document = docs_service.documents().get(documentId=document_id).execute()
            
            # Find the new row's cells
            table = None
            new_row_cells = []
            
            for element in updated_document.get('body').get('content'):
                if 'table' in element:
                    table = element.get('table')
                    # Get the last row's cells
                    last_row = table.get('tableRows')[-1]
                    for cell in last_row.get('tableCells'):
                        new_row_cells.append(cell.get('startIndex'))
            
            if new_row_cells:
                # Insert data into the new cells
                data_requests = []
                
                for i, cell_data in enumerate(record_data):
                    if i < len(new_row_cells):
                        data_requests.append({
                            'insertText': {
                                'location': {
                                    'index': new_row_cells[i] + 1  # +1 to get inside the cell
                                },
                                'text': str(cell_data)
                            }
                        })
                
                # Apply the changes
                docs_service.documents().batchUpdate(
                    documentId=document_id,
                    body={'requests': data_requests}
                ).execute()
                
                print(f"Added new record to document {document_id}")
                return True
            
        return False
        
    except Exception as e:
        print(f"Error adding record to Google Doc: {str(e)}")
        return False

if __name__ == "__main__":
    # Create a new document with a table
    result = create_table_in_google_doc()
    
    if result['success']:
        # Add a new record to the document
        document_id = result['document_id']
        print("\nAdding a new record to the document...")
        
        new_record = ["Charlie Davis", "charlie@example.com", "555-7890", "2023-05-05"]
        add_record_to_doc(document_id, new_record) 