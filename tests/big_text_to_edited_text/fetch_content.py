import os
import sys
from google_doc_fetcher import fetch_google_doc

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fetch_content.py DOC_ID")
        sys.exit(1)
    
    doc_id = sys.argv[1]
    print(f"Fetching document {doc_id}...")
    
    try:
        content = fetch_google_doc(doc_id)
        output_file = "document.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Document content saved to {output_file}")
        print(f"Content length: {len(content)} characters")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 