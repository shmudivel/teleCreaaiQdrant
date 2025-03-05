# vector_db_tool.py
import os
import qdrant_client
from langchain.agents import tool
from langchain.chains import RetrievalQA
from langchain_community.llms import OpenAI
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.tools import BaseTool
from qdrant_client.http import models
from dotenv import load_dotenv
import logging
from typing import Any, Optional

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDBToolset:
    """Tools for interacting with the vector database."""
    
    def __init__(self):
        """Initialize the vector database client."""
        try:
            # Connect to Qdrant
            self.client = qdrant_client.QdrantClient(
                url=os.getenv("QDRANT_URL", "http://qdrant:6333"),
                api_key=os.getenv("QDRANT_API_KEY", "")
            )
            
            # Check if the collection exists
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if "knowledge_base" not in collection_names:
                # Create the collection if it doesn't exist
                self.client.create_collection(
                    collection_name="knowledge_base",
                    vectors_config=models.VectorParams(
                        size=1536,  # OpenAI embeddings dimension
                        distance=models.Distance.COSINE
                    )
                )
                logger.info("Created 'knowledge_base' collection")
            
            # Initialize the vector store
            embeddings = OpenAIEmbeddings()
            self.vector_store = Qdrant(
                client=self.client,
                collection_name="knowledge_base",
                embeddings=embeddings
            )
            
            # Build RetrievalQA with configurable LLM
            self.qa_chain = self._create_qa_chain()
        
        except Exception as e:
            logger.error(f"Error initializing vector database: {str(e)}")
            # Create a dummy client for fallback
            self.client = None
            self.vector_store = None
            self.qa_chain = None

    def _create_qa_chain(self):
        llm = self._get_llm()
        return RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever()
        )

    def _get_llm(self):
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        model_name = os.getenv("LLM_MODEL", "gpt-4o-2024-11-20")

        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model_name=model_name,
                temperature=0.3
            )
        else:  # Default to OpenAI
            from langchain_community.chat_models import ChatOpenAI
            return ChatOpenAI(
                model_name=model_name,
                temperature=0.3
            )

    @tool
    def vector_db_query(self, query: str) -> str:
        """
        Query the Qdrant vector store for relevant context and get an answer from the LLM.

        IMPORTANT:
        - Do NOT pass 'self' in the JSON input. Just pass {"query": "<text>"}
        - Python will automatically handle the 'self' argument internally.
        """
        if self.qa_chain:
            return self.qa_chain.run(query)
        return "Vector database is not available."

    def search_knowledge_base(self, query, limit=5):
        """Search the knowledge base for relevant information."""
        try:
            if not self.client or not self.vector_store:
                return "Vector database is not available."
            
            # For now, return a placeholder response
            # In a real implementation, you would:
            # 1. Convert the query to an embedding
            # 2. Search the vector database
            # 3. Return the results
            
            return f"Found information related to '{query}' in the knowledge base."
        
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            return f"Error searching knowledge base: {str(e)}"
    
    def tools(self):
        """Return properly formatted tools"""
        return [
            self.vector_db_query,  # Use the @tool decorated method
            self.create_search_tool()  # Add this new method
        ]
    
    def create_search_tool(self):
        """Create a search tool with proper interface"""
        @tool
        def search_tool(query: str) -> str:
            """Search the knowledge base (name and description now come from docstring)"""
            return self.search_knowledge_base(query)
        
        # Manually set the name and description
        search_tool.name = "search_knowledge_base"
        search_tool.description = "Search the knowledge base for information related to a query"
        return search_tool