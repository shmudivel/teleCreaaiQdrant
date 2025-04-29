import os
import re
from googleapiclient.discovery import build
from google.oauth2 import service_account
import anthropic
import argparse
from urllib.parse import urlparse, parse_qs
import datetime
from .prompts import DOC_ANALYSIS_PROMPT, DOC_ANALYSIS_SYSTEM_PROMPT
from .api_utils import create_claude_client, call_claude_api, exponential_backoff_retry

# Google API scopes needed
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

# Hard-coded Anthropic API key from env. file
ANTHROPIC_API_KEY = "REMOVED_API_KEY"

def extract_doc_id_from_url(url):
    """Extract the document ID from a Google Docs URL."""
    parsed_url = urlparse(url)
    
    # Handle different URL formats
    if 'document/d/' in url:
        # Format: https://docs.google.com/document/d/DOCUMENT_ID/edit
        match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', url)
        if match:
            return match.group(1)
    elif 'docs.google.com' in parsed_url.netloc:
        # Check for doc ID in query parameters
        query_params = parse_qs(parsed_url.query)
        if 'id' in query_params:
            return query_params['id'][0]
    
    raise ValueError("Could not extract document ID from the provided URL")

def get_google_credentials(service_account_file):
    """Get credentials from service account file."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES)
        return credentials
    except Exception as e:
        print(f"Error loading service account credentials: {str(e)}")
        raise

def get_document_content(doc_id, service_account_file):
    """Retrieve the content of a Google Doc by its ID."""
    creds = get_google_credentials(service_account_file)
    service = build('docs', 'v1', credentials=creds)
    
    # Get the document
    document = service.documents().get(documentId=doc_id).execute()
    
    # Extract text content
    content = ""
    for element in document.get('body').get('content'):
        if 'paragraph' in element:
            for para_element in element.get('paragraph').get('elements'):
                if 'textRun' in para_element:
                    content += para_element.get('textRun').get('content')
    
    return content

@exponential_backoff_retry()
def analyze_with_claude(text):
    """Analyze text using Claude 3.7 and divide it into topical sections."""
    client = create_claude_client(ANTHROPIC_API_KEY)
    
    result = call_claude_api(
        client=client,
        model="claude-3-7-sonnet-20250219",
        prompt=f"{DOC_ANALYSIS_PROMPT}\n\nText:\n{text}",
        system=DOC_ANALYSIS_SYSTEM_PROMPT,
        max_tokens=8000,
        temperature=0
    )
    
    # Remove any introductory text before the actual content
    intro_patterns = [
        "Here is the text divided into distinct topical sections with divider lines inserted:",
        "Here's the text with divider lines inserted at topic transitions:",
        "Here is the original text with divider lines inserted at topic transitions:",
        "Here is the text with divider lines inserted at natural topic transitions:"
    ]
    
    for pattern in intro_patterns:
        if result.strip().startswith(pattern):
            result = result.replace(pattern, "", 1).strip()
    
    # Remove any empty lines at the beginning
    result = result.lstrip("\n")
    
    return result.strip()

def main():
    parser = argparse.ArgumentParser(description='Analyze Google Docs content with Claude 3.5')
    parser.add_argument('--url', required=True, help='Google Doc URL to analyze')
    parser.add_argument('--service-account-file', required=True, help='Path to service account JSON file')
    
    args = parser.parse_args()
    
    try:
        # Extract document ID from URL
        doc_id = extract_doc_id_from_url(args.url)
        print(f"Extracting content from document ID: {doc_id}")
        
        # Get document content
        content = get_document_content(doc_id, args.service_account_file)
        print(f"Retrieved {len(content)} characters from the document")
        
        # Analyze with Claude
        print("Analyzing content with Claude 3.5...")
        analyzed_text = analyze_with_claude(content)
        
        # Create output file in same directory as this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(script_dir, f"analyzed_doc_{timestamp}.txt")
        
        # Write the analyzed text to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(analyzed_text)
        
        print(f"Analysis written to {output_file}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 