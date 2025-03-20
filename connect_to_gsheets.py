"""
Google Sheets Connection Example

This script demonstrates how to connect to Google Sheets and create a record.
Before running this script, make sure to enable the Google Sheets API:

1. Go to https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=514717665212
2. Click "Enable API" button
3. Wait a few minutes for the change to propagate
4. Run this script
"""

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

def connect_to_sheets_and_create_record():
    """
    Connect to Google Sheets and create a record.
    """
    # Load credentials from the service account file
    credentials = service_account.Credentials.from_service_account_file(
        'bustling-folio-439811-h8-539f8ab05fa7.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )

    try:
        # Build the Sheets API service
        sheets_service = build('sheets', 'v4', credentials=credentials)
        
        # Create a new spreadsheet
        spreadsheet_body = {
            'properties': {
                'title': 'Test Data Spreadsheet'
            },
            'sheets': [
                {
                    'properties': {
                        'title': 'Data Records'
                    }
                }
            ]
        }
        
        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
        spreadsheet_id = spreadsheet['spreadsheetId']
        
        print(f"Created new spreadsheet with ID: {spreadsheet_id}")
        print(f"Spreadsheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        
        # Add header row to the spreadsheet
        range_name = 'Data Records!A1:D1'
        header_values = [
            ['Name', 'Email', 'Phone', 'Date']
        ]
        
        header_body = {
            'values': header_values
        }
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=header_body
        ).execute()
        
        # Format the header row to be bold and frozen
        requests = [
            # Make header bold
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat.textFormat.bold'
                }
            },
            # Freeze the header row
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': 0,
                        'gridProperties': {
                            'frozenRowCount': 1
                        }
                    },
                    'fields': 'gridProperties.frozenRowCount'
                }
            }
        ]
        
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        # Add a new record to the spreadsheet
        record_range = 'Data Records!A2:D2'
        record_values = [
            ['John Doe', 'john@example.com', '555-1234', '2023-05-01']
        ]
        
        record_body = {
            'values': record_values
        }
        
        result = sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=record_range,
            valueInputOption='RAW',
            body=record_body
        ).execute()
        
        print(f"Added new record, updated {result.get('updatedCells')} cells.")
        
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
        print("Google Sheets connection test successful!")
        
        # Add more records
        more_records_range = 'Data Records!A3:D5'
        more_records_values = [
            ['Jane Smith', 'jane@example.com', '555-5678', '2023-05-02'],
            ['Bob Johnson', 'bob@example.com', '555-9012', '2023-05-03'],
            ['Alice Brown', 'alice@example.com', '555-3456', '2023-05-04']
        ]
        
        more_records_body = {
            'values': more_records_values
        }
        
        result = sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=more_records_range,
            valueInputOption='RAW',
            body=more_records_body
        ).execute()
        
        print(f"Added additional records, updated {result.get('updatedCells')} cells.")
        
        return {
            'success': True,
            'spreadsheet_id': spreadsheet_id,
            'url': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        }
        
    except HttpError as error:
        if "API has not been used" in str(error) or "is disabled" in str(error):
            print("\nERROR: The Google Sheets API is not enabled for this project.")
            print("Please enable it by visiting:")
            print("https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=514717665212")
            print("\nAfter enabling, wait a few minutes for the change to propagate before running this script again.")
        else:
            print(f"An HTTP error occurred: {error}")
        return {'success': False, 'error': str(error)}
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {'success': False, 'error': str(e)}

def add_new_record(spreadsheet_id, record_data):
    """
    Add a new record to an existing spreadsheet.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
        record_data: List containing the record values [name, email, phone, date]
    """
    # Load credentials from the service account file
    credentials = service_account.Credentials.from_service_account_file(
        'bustling-folio-439811-h8-539f8ab05fa7.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    
    try:
        # Build the Sheets API service
        sheets_service = build('sheets', 'v4', credentials=credentials)
        
        # Get the current data to find the next empty row
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='Data Records!A:D'
        ).execute()
        
        values = result.get('values', [])
        next_row = len(values) + 1  # +1 because rows are 1-indexed
        
        # Add the new record
        range_name = f'Data Records!A{next_row}:D{next_row}'
        body = {
            'values': [record_data]
        }
        
        result = sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"Added new record in row {next_row}, updated {result.get('updatedCells')} cells.")
        return True
        
    except Exception as e:
        print(f"Error adding record: {str(e)}")
        return False

if __name__ == "__main__":
    print("Connecting to Google Sheets and creating a record...")
    result = connect_to_sheets_and_create_record()
    
    if result['success']:
        # Add another record
        print("\nAdding an additional record...")
        new_record = ["Charlie Davis", "charlie@example.com", "555-7890", "2023-05-05"]
        add_new_record(result['spreadsheet_id'], new_record) 