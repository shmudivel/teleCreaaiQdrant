import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from src.platforms.vector_db import VectorDBIntegration

def main():
    """
    Example of using the VectorDBIntegration to process user queries
    with vector DB context retrieval and agent-based response generation.
    """
    # User query to process
    user_query = "Как развивать карьеру в IT компании?"
    
    print(f"Processing query: {user_query}")
    print("\n" + "-" * 50 + "\n")
    
    # Initialize the integration
    integration = VectorDBIntegration(collection_name="context-main3", top_k=3)
    
    # Process the query and get a response
    response = integration.process_query(user_query)
    
    print("\n" + "-" * 50 + "\n")
    print("Final response:")
    print(response)

if __name__ == "__main__":
    main() 