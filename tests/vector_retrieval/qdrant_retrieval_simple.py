import os
import json
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_qdrant import Qdrant
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document

# Load environment variables
load_dotenv()

def retrieve_from_qdrant(prompt, verbose=True, show_full_content=True):
    """
    Retrieve information from Qdrant vector database based on a prompt.
    
    Args:
        prompt (str): The prompt/query to search for
        verbose (bool): Whether to print detailed retrieval logs
        show_full_content (bool): Whether to show the full document content (default True)
        
    Returns:
        str: The retrieved information
    """
    # Connect to Qdrant
    qdrant_url = os.getenv("QDRANT_HOST")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = "context-main3"  # Use the specified collection
    
    if verbose:
        print("\n[LOG] Connecting to Qdrant vector database...")
        print(f"[LOG] URL: {qdrant_url}")
        print(f"[LOG] Collection: {collection_name}")
    
    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
    )
    
    # Initialize OpenAI embeddings and LLM
    embeddings = OpenAIEmbeddings()
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.2
    )
    
    # Initialize vector store
    vector_store = Qdrant(
        client=client,
        collection_name=collection_name,
        embeddings=embeddings,
    )
    
    # Create retrieval chain
    retriever = vector_store.as_retriever(
        search_kwargs={"k": 3}  # Return top 3 matches
    )
    
    # First, get the raw documents to log them
    if verbose:
        print("[LOG] Retrieving documents from Qdrant...")
        
    # Get raw documents from retriever
    raw_docs = retriever.get_relevant_documents(prompt)
    
    if verbose:
        print(f"[LOG] Retrieved {len(raw_docs)} documents from Qdrant")
        print("[LOG] Retrieved documents:")
        
        for i, doc in enumerate(raw_docs):
            # Clean up metadata for display
            metadata = doc.metadata.copy() if hasattr(doc, 'metadata') else {}
            
            # Remove potentially large binary fields from metadata for display
            if 'vector' in metadata:
                metadata['vector'] = '[VECTOR DATA TRUNCATED]'
                
            print(f"\n[LOG] Document {i+1}:")
            print(f"[LOG] Metadata: {json.dumps(metadata, indent=2, default=str)}")
            
            # Get document content
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            
            if show_full_content:
                # Show the full content
                print(f"[LOG] Full Content ({len(content)} chars):")
                print("-" * 40)
                print(content)
                print("-" * 40)
            else:
                # Show truncated content (first 200 chars)
                print(f"[LOG] Content (truncated): {content[:200]}...")
                if len(content) > 200:
                    print(f"[LOG] ...content continues ({len(content)} chars total)")
                    print(f"[LOG] To see full content, use 'full:' prefix with your query")
    
    # Create and run QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        verbose=verbose,
        return_source_documents=verbose
    )
    
    # Retrieve information based on the prompt
    if verbose:
        print("\n[LOG] Sending retrieved documents to LLM for processing...")
    
    response = qa_chain.invoke(prompt)
    
    if verbose and 'source_documents' in response:
        print(f"\n[LOG] Sources used by LLM: {len(response['source_documents'])} documents")
        
    return response["result"]

def main():
    """
    Main function to demonstrate retrieval from Qdrant.
    """
    # Predefined prompts
    prompts = [
        "What are the main features of this product?",
        "Explain the technical architecture of the system.",
        "What are the key benefits of using this solution?"
    ]
    
    print("Qdrant Vector DB Retrieval Demo")
    print("================================")
    print(f"Collection: context-main3\n")
    
    # Test retrieval with predefined prompts
    for prompt in prompts:
        print(f"\nPrompt: {prompt}")
        print("-" * 40)
        
        try:
            result = retrieve_from_qdrant(prompt, verbose=True, show_full_content=True)
            print(f"\nFinal Response: {result}\n")
            print("-" * 80)
        except Exception as e:
            print(f"Error retrieving information: {str(e)}\n")
    
    # Interactive mode
    print("\nInteractive Mode (type 'exit' to quit)")
    print("-" * 40)
    
    # Set verbose logging to true by default
    verbose = True
    # Show full content by default
    show_full_content = True
    print("\n[INFO] Detailed retrieval logs are enabled by default")
    print("[INFO] Full document content is shown by default")
    print("[INFO] To disable logs for any query, start your prompt with 'quiet:'")
    print("[INFO] To show truncated content, start your prompt with 'brief:'")
    
    while True:
        user_prompt = input("\nEnter your prompt (or 'exit' to quit): ")
        
        if user_prompt.lower() in ["exit", "quit"]:
            break
        
        # Check for special prefixes
        current_verbose = verbose
        current_show_full = show_full_content
        
        if user_prompt.lower().startswith("quiet:"):
            current_verbose = False
            user_prompt = user_prompt[6:].strip()  # Remove the 'quiet:' prefix
            print("[INFO] Running in quiet mode (no logs) for this query")
            
        elif user_prompt.lower().startswith("brief:"):
            current_show_full = False
            user_prompt = user_prompt[6:].strip()  # Remove the 'brief:' prefix
            print("[INFO] Showing truncated content for this query")
        
        try:
            result = retrieve_from_qdrant(user_prompt, verbose=current_verbose, show_full_content=current_show_full)
            print(f"\nFinal Response: {result}")
        except Exception as e:
            print(f"\nError retrieving information: {str(e)}")

if __name__ == "__main__":
    main() 