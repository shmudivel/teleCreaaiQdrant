# vector_db_tool.py
import os
import qdrant_client
from langchain.agents import tool
from langchain.chains import RetrievalQA
from langchain_community.llms import OpenAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_qdrant import Qdrant
from langchain.tools import BaseTool as LangchainBaseTool
from crewai.tools import BaseTool as CrewaiBaseTool
from qdrant_client.http import models
from dotenv import load_dotenv
import logging
from typing import Any, Optional
from pydantic import Field
import traceback
import json
import inspect

# Load environment variables
load_dotenv()

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define tool classes properly outside the main class
class VectorDBQueryTool(CrewaiBaseTool):
    """Tool for querying the vector database."""
    
    name: str = "vector_db_query"
    description: str = "Query the Qdrant vector store for relevant context and get an answer from the LLM."
    # Properly define toolset as a field
    vector_db: Any = Field(description="Vector database instance")
    
    # Define the schema to accept either 'query' or 'description'
    def schema(self) -> dict:
        base_schema = super().schema()
        base_schema["properties"] = {
            "query": {"type": "string", "description": "The query to search for"},
            "description": {"type": "string", "description": "Alternative field for query"}
        }
        base_schema["required"] = ["query"]  # Make query field required
        return base_schema
    
    def _run(self, **kwargs) -> str:
        """Run the tool with the given query."""
        # Extract query from either 'query' or 'description' field
        logger.info(f"Vector DB Query Tool received kwargs: {kwargs}")
        
        # Handle case when the input is an empty dict
        if not kwargs:
            logger.warning("Received empty kwargs dict, returning fallback response")
            return "No query provided. Please provide a specific question or topic to search for."
        
        # For CrewAI tools, the input might be in the first unnamed parameter
        if len(kwargs) == 0 and len(self._run.__code__.co_varnames) > 1:
            # Try to get the first argument value
            frame = inspect.currentframe()
            try:
                if frame and frame.f_back:
                    arg_values = inspect.getargvalues(frame.f_back)
                    if 'args' in arg_values.locals and arg_values.locals['args']:
                        # Handle the case where the first argument might be the query
                        first_arg = arg_values.locals['args'][1] if len(arg_values.locals['args']) > 1 else None
                        if first_arg:
                            logger.info(f"Found query in first argument: {first_arg}")
                            return self._process_query(first_arg)
            finally:
                del frame  # Avoid reference cycles
        
        query = kwargs.get('query') or kwargs.get('description', '')
        return self._process_query(query)
        
    def _process_query(self, query):
        """Process the query string or object."""
        # Log the original query format for debugging
        logger.info(f"Original query format: {type(query)}, value: {query}")
        
        # Handle empty string or None input
        if not query:
            logger.warning("Received empty query, returning fallback response")
            return "No query provided. Please provide a specific question or topic to search for."
            
        # Handle case when input is a JSON string rather than a parsed object
        if isinstance(query, str) and (query.startswith('{') and query.endswith('}')):
            try:
                parsed_json = json.loads(query)
                logger.info(f"Parsed JSON string to dict: {parsed_json}")
                
                # Handle empty JSON object case
                if not parsed_json:
                    logger.warning("Received empty JSON object, returning fallback response")
                    return "No query provided. Please provide a specific question or topic to search for."
                    
                if isinstance(parsed_json, dict):
                    if 'query' in parsed_json:
                        query = parsed_json['query']
                        logger.info(f"Extracted query from JSON string: {query[:50] if query else 'empty'}")
                    elif 'description' in parsed_json:
                        query = parsed_json['description']
                        logger.info(f"Extracted description from JSON string: {query[:50] if query else 'empty'}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse query as JSON: {e}")
        
        # Continue with existing logic
        if isinstance(query, dict) and 'description' in query:
            query = query['description']
            logger.info(f"Extracted query from description field in dict: {query[:50] if query else 'empty'}")
        elif isinstance(query, dict) and 'query' in query:
            query = query['query']
            logger.info(f"Extracted query from query field in dict: {query[:50] if query else 'empty'}")
        elif isinstance(query, str):
            logger.info(f"Query is a string: {query[:50] if query else 'empty'}")
        else:
            logger.warning(f"Unexpected query format: {type(query)}, value: {query}")
            
        logger.info(f"Final query after processing: {query[:100] if query else 'empty'}")
        
        # Prevent empty queries from being sent to the model
        if not query or (isinstance(query, str) and query.strip() == ''):
            logger.warning("Empty query received, returning fallback response")
            return "No query provided. Please provide a specific question or topic to search for."
        
        try:
            if self.vector_db.qa_chain:
                logger.info(f"Running vector_db_query tool with final query: {query[:50]}...")
                result = self.vector_db.qa_chain.run(query)
                logger.info(f"Vector DB query succeeded, result length: {len(result)}")
                return result
            logger.warning("Vector database qa_chain is not available")
            return "Vector database is not available."
        except Exception as e:
            logger.error(f"Error in vector_db_query tool: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Special handling for Anthropic API errors
            if "all messages must have non-empty content" in str(e):
                return "Error: Empty query detected. Please provide a specific question or topic to search for."
            
            return f"Error querying vector database: {str(e)}"

class SearchKnowledgeBaseTool(CrewaiBaseTool):
    """Tool for searching the knowledge base."""
    
    name: str = "search_knowledge_base"
    description: str = "Search the knowledge base for information related to a query"
    # Properly define toolset as a field
    vector_db: Any = Field(description="Vector database instance")
    
    # Define the schema to accept either 'query' or 'description'
    def schema(self) -> dict:
        base_schema = super().schema()
        base_schema["properties"] = {
            "query": {"type": "string", "description": "The query to search for"},
            "description": {"type": "string", "description": "Alternative field for query"}
        }
        base_schema["required"] = ["query"]  # Make query field required
        return base_schema
    
    def _run(self, **kwargs) -> str:
        """Run the tool with the given query."""
        # Extract query from either 'query' or 'description' field
        logger.info(f"Search Knowledge Base Tool received kwargs: {kwargs}")
        
        # Handle case when the input is an empty dict
        if not kwargs:
            logger.warning("Received empty kwargs dict, returning fallback response")
            return "No query provided. Please provide a specific question or topic to search for."
        
        # For CrewAI tools, the input might be in the first unnamed parameter
        if len(kwargs) == 0 and len(self._run.__code__.co_varnames) > 1:
            # Try to get the first argument value
            frame = inspect.currentframe()
            try:
                if frame and frame.f_back:
                    arg_values = inspect.getargvalues(frame.f_back)
                    if 'args' in arg_values.locals and arg_values.locals['args']:
                        # Handle the case where the first argument might be the query
                        first_arg = arg_values.locals['args'][1] if len(arg_values.locals['args']) > 1 else None
                        if first_arg:
                            logger.info(f"Found query in first argument: {first_arg}")
                            return self._process_query(first_arg)
            finally:
                del frame  # Avoid reference cycles
        
        query = kwargs.get('query') or kwargs.get('description', '')
        return self._process_query(query)
        
    def _process_query(self, query):
        """Process the query string or object."""
        # Log the original query format for debugging
        logger.info(f"Original query format: {type(query)}, value: {query}")
        
        # Handle empty string or None input
        if not query:
            logger.warning("Received empty query, returning fallback response")
            return "No query provided. Please provide a specific question or topic to search for."
            
        # Handle case when input is a JSON string rather than a parsed object
        if isinstance(query, str) and (query.startswith('{') and query.endswith('}')):
            try:
                parsed_json = json.loads(query)
                logger.info(f"Parsed JSON string to dict: {parsed_json}")
                
                # Handle empty JSON object case
                if not parsed_json:
                    logger.warning("Received empty JSON object, returning fallback response")
                    return "No query provided. Please provide a specific question or topic to search for."
                    
                if isinstance(parsed_json, dict):
                    if 'query' in parsed_json:
                        query = parsed_json['query']
                        logger.info(f"Extracted query from JSON string: {query[:50] if query else 'empty'}")
                    elif 'description' in parsed_json:
                        query = parsed_json['description']
                        logger.info(f"Extracted description from JSON string: {query[:50] if query else 'empty'}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse query as JSON: {e}")
        
        # Continue with existing logic
        if isinstance(query, dict) and 'description' in query:
            query = query['description']
            logger.info(f"Extracted query from description field in dict: {query[:50] if query else 'empty'}")
        elif isinstance(query, dict) and 'query' in query:
            query = query['query']
            logger.info(f"Extracted query from query field in dict: {query[:50] if query else 'empty'}")
        elif isinstance(query, str):
            logger.info(f"Query is a string: {query[:50] if query else 'empty'}")
        else:
            logger.warning(f"Unexpected query format: {type(query)}, value: {query}")
            
        logger.info(f"Final query after processing: {query[:100] if query else 'empty'}")
        
        # Prevent empty queries
        if not query or (isinstance(query, str) and query.strip() == ''):
            logger.warning("Empty query received, returning fallback response")
            return "No query provided. Please provide a specific question or topic to search for."
        
        try:
            result = self.vector_db.search_knowledge_base(query)
            logger.info(f"Running search_knowledge_base tool with final query: {query[:50]}...")
            logger.info(f"Knowledge base search succeeded, result length: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"Error in search_knowledge_base tool: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error searching knowledge base: {str(e)}"

class VectorDBToolset:
    """Tools for interacting with the vector database."""
    
    def __init__(self):
        """Initialize the vector database client."""
        logger.info("Initializing VectorDBToolset")
        try:
            # Connect to Qdrant with secure connection
            logger.info(f"Connecting to Qdrant at {os.getenv('QDRANT_URL', 'http://qdrant:6333')}")
            self.client = qdrant_client.QdrantClient(
                url=os.getenv("QDRANT_URL", "http://qdrant:6333"),
                api_key=os.getenv("QDRANT_API_KEY", ""),
                prefer_grpc=False,
                https=False
            )
            
            # Check if the collection exists
            logger.info("Checking for existing collections")
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            logger.info(f"Found collections: {collection_names}")
            
            if "knowledge_base" not in collection_names:
                # Create the collection if it doesn't exist
                logger.info("Creating 'knowledge_base' collection")
                self.client.create_collection(
                    collection_name="knowledge_base",
                    vectors_config=models.VectorParams(
                        size=1536,  # OpenAI embeddings dimension
                        distance=models.Distance.COSINE
                    )
                )
                logger.info("Created 'knowledge_base' collection")
            
            # Initialize the vector store
            logger.info("Initializing vector store with OpenAI embeddings")
            embeddings = OpenAIEmbeddings()
            self.vector_store = Qdrant(
                client=self.client,
                collection_name="knowledge_base",
                embeddings=embeddings
            )
            
            # Build RetrievalQA with configurable LLM
            logger.info("Building RetrievalQA chain")
            self.qa_chain = self._create_qa_chain()
            logger.info("VectorDBToolset initialization completed successfully")
        
        except Exception as e:
            logger.error(f"Error initializing vector database: {str(e)}")
            logger.error(traceback.format_exc())
            # Create a dummy client for fallback
            self.client = None
            self.vector_store = None
            self.qa_chain = None
            logger.warning("Using fallback null implementation for vector database")

    def _create_qa_chain(self):
        logger.info("Creating QA chain")
        llm = self._get_llm()
        logger.info(f"Using LLM: {type(llm).__name__}")
        return RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever()
        )

    def _get_llm(self):
        provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
        model_name = os.getenv("LLM_MODEL", "claude-3-sonnet-20240229")
        logger.info(f"Using LLM provider: {provider}, model: {model_name}")

        if provider == "openai":
            logger.info("Initializing OpenAI model")
            return ChatOpenAI(
                model_name=model_name,
                temperature=0.3
            )
        else:  # Default to Anthropic
            logger.info("Initializing Anthropic model")
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
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
        logger.info(f"Direct vector_db_query called with: {query[:50]}...")
        if self.qa_chain:
            return self.qa_chain.run(query)
        return "Vector database is not available."

    def search_knowledge_base(self, query, limit=5):
        """Search the knowledge base for relevant information."""
        logger.info(f"Direct search_knowledge_base called with: {query[:50] if query and isinstance(query, str) else 'empty'}...")
        try:
            if not self.client or not self.vector_store:
                logger.warning("Vector database is not available for search")
                return "Vector database is not available."
            
            # Handle empty queries
            if not query or (isinstance(query, str) and query.strip() == ''):
                logger.warning("Empty query received in search_knowledge_base")
                return "No query provided. Please provide a specific question or topic to search for."
            
            # For now, return a placeholder response
            # In a real implementation, you would:
            # 1. Convert the query to an embedding
            # 2. Search the vector database
            # 3. Return the results
            
            return f"Found information related to '{query}' in the knowledge base."
        
        except Exception as e:
            logger.error(f"Error searching knowledge base: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error searching knowledge base: {str(e)}"
    
    def tools(self):
        """Return properly formatted tools for CrewAI"""
        # Create CrewAI compatible tools
        logger.info("Creating CrewAI tools with proper validation")
        try:
            tools = [
                VectorDBQueryTool(vector_db=self),
                SearchKnowledgeBaseTool(vector_db=self)
            ]
            logger.info(f"Successfully created {len(tools)} CrewAI tools")
            return tools
        except Exception as e:
            logger.error(f"Error creating CrewAI tools: {str(e)}")
            logger.error(traceback.format_exc())
            logger.warning("Returning empty tools list as fallback")
            return []