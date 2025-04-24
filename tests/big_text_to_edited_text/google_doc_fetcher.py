import os
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Path to service account credentials
SERVICE_ACCOUNT_FILE = '/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/bustling-folio-439811-h8-539f8ab05fa7.json'

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

def get_credentials():
    """Get valid service account credentials.
    
    Returns:
        Credentials, the obtained credential.
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return credentials
    except Exception as e:
        print(f"Error loading service account credentials: {e}")
        return None

def fetch_google_doc(doc_id):
    """Fetches the content of a Google Doc by its ID.
    
    Args:
        doc_id: The ID of the Google Doc to fetch.
        
    Returns:
        The text content of the document.
    """
    try:
        # Try to use Google API with service account
        creds = get_credentials()
        service = build('docs', 'v1', credentials=creds)
        document = service.documents().get(documentId=doc_id).execute()
        
        doc_content = ''
        for content in document.get('body').get('content'):
            if 'paragraph' in content:
                for element in content.get('paragraph').get('elements'):
                    if 'textRun' in element:
                        doc_content += element.get('textRun').get('content')
        
        return doc_content
        
    except Exception as e:
        print(f"Error using Google API: {e}")
        print("Trying alternative method (public docs only)...")
        
        # Alternative method for public documents
        try:
            # Try to access as a publicly shared Google Doc
            url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
            response = requests.get(url)
            if response.status_code == 200:
                return response.text
            else:
                raise Exception(f"Failed to fetch document: HTTP {response.status_code}")
        except Exception as alt_e:
            print(f"Alternative method failed: {alt_e}")
            print("Please ensure the document is publicly accessible or authorize the API access.")
            raise

if __name__ == "__main__":
    # Test the function if this file is run directly
    import sys
    if len(sys.argv) > 1:
        doc_id = sys.argv[1]
        print(f"Fetching document {doc_id}...")
        content = fetch_google_doc(doc_id)
        print(f"Document content (first 500 chars):\n{content[:500]}...") 