import os
import json
import unittest
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_qdrant import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

# Load environment variables
load_dotenv()

class QdrantRetrievalTest(unittest.TestCase):
    """
    Test case for retrieving data from Qdrant vector database based on prompts.
    This specifically tests retrieval from the 'context-main3' collection.
    """
    
    def setUp(self):
        """Initialize the Qdrant client and vector store for testing."""
        # Connect to Qdrant
        self.qdrant_url = os.getenv("QDRANT_HOST")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = "context-main3"  # Use the specified collection
        
        print(f"\n[LOG] Connecting to Qdrant at {self.qdrant_url}")
        print(f"[LOG] Using collection: {self.collection_name}")
        
        self.client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
        )
        
        # Initialize OpenAI embeddings and LLM
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.2
        )
        
        # Initialize vector store
        self.vector_store = Qdrant(
            client=self.client,
            collection_name=self.collection_name,
            embeddings=self.embeddings,
        )
        
        # Create retrieval chain
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 3}  # Return top 3 matches
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            verbose=True
        )
    
    def test_simple_retrieval(self):
        """Test retrieval from vector database with a simple prompt."""
        # Simple test prompt
        prompt = "What are the main features of this product?"
        
        print(f"\n[LOG] Testing retrieval with prompt: '{prompt}'")
        
        # Get raw documents first to show what was retrieved
        print("\n[LOG] Getting raw documents from retriever...")
        docs = self.retriever.get_relevant_documents(prompt)
        
        print(f"[LOG] Retrieved {len(docs)} documents")
        for i, doc in enumerate(docs):
            # Prepare metadata for display (remove large binary fields)
            metadata = doc.metadata.copy() if hasattr(doc, 'metadata') else {}
            if 'vector' in metadata:
                metadata['vector'] = '[VECTOR DATA TRUNCATED]'
                
            print(f"\n[LOG] Document {i+1}:")
            print(f"[LOG] Metadata: {json.dumps(metadata, indent=2, default=str)}")
            
            # Show truncated content
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            print(f"[LOG] Content (truncated): {content[:200]}...")
            if len(content) > 200:
                print(f"[LOG] ...content continues ({len(content)} chars total)")
        
        # Retrieve information based on the prompt
        print("\n[LOG] Sending retrieved documents to LLM for processing...")
        response = self.qa_chain.invoke(prompt)
        
        # Basic validation
        self.assertIsNotNone(response)
        self.assertIsInstance(response, dict)
        self.assertIn("result", response)
        
        # Log source documents used by LLM
        if "source_documents" in response:
            print(f"\n[LOG] Sources used by LLM: {len(response['source_documents'])} documents")
        
        print(f"\nPrompt: {prompt}")
        print(f"Final Response: {response['result']}")
    
    def test_specific_retrieval(self):
        """Test retrieval with a more specific prompt."""
        # More specific prompt
        prompt = "Explain the technical architecture of the system."
        
        print(f"\n[LOG] Testing retrieval with prompt: '{prompt}'")
        
        # Get raw documents first to show what was retrieved
        print("\n[LOG] Getting raw documents from retriever...")
        docs = self.retriever.get_relevant_documents(prompt)
        
        print(f"[LOG] Retrieved {len(docs)} documents")
        for i, doc in enumerate(docs):
            # Prepare metadata for display (remove large binary fields)
            metadata = doc.metadata.copy() if hasattr(doc, 'metadata') else {}
            if 'vector' in metadata:
                metadata['vector'] = '[VECTOR DATA TRUNCATED]'
                
            print(f"\n[LOG] Document {i+1}:")
            print(f"[LOG] Metadata: {json.dumps(metadata, indent=2, default=str)}")
            
            # Show truncated content
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            print(f"[LOG] Content (truncated): {content[:200]}...")
            if len(content) > 200:
                print(f"[LOG] ...content continues ({len(content)} chars total)")
        
        # Retrieve information based on the prompt
        print("\n[LOG] Sending retrieved documents to LLM for processing...")
        response = self.qa_chain.invoke(prompt)
        
        # Basic validation
        self.assertIsNotNone(response)
        self.assertIsInstance(response, dict)
        self.assertIn("result", response)
        
        # Log source documents used by LLM
        if "source_documents" in response:
            print(f"\n[LOG] Sources used by LLM: {len(response['source_documents'])} documents")
        
        print(f"\nPrompt: {prompt}")
        print(f"Final Response: {response['result']}")

if __name__ == "__main__":
    unittest.main() 