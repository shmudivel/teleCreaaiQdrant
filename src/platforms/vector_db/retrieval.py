import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_qdrant import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
import logging

# Get logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class QdrantRetriever:
    """Class for retrieving data from Qdrant vector database."""
    
    def __init__(self, collection_name="context-main3", top_k=3):
        """Initialize the Qdrant client and vector store."""
        logger.info(f"Initializing QdrantRetriever with collection: {collection_name}, top_k: {top_k}")
        
        # Connect to Qdrant
        self.qdrant_url = os.getenv("QDRANT_HOST")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = collection_name
        self.top_k = top_k
        
        logger.info(f"Connecting to Qdrant at {self.qdrant_url}, collection: {self.collection_name}")
        
        # Initialize client
        self.client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
        )
        
        # Initialize OpenAI embeddings
        logger.info("Initializing OpenAI embeddings")
        self.embeddings = OpenAIEmbeddings()
        
        # Initialize vector store
        logger.info("Initializing Qdrant vector store")
        self.vector_store = Qdrant(
            client=self.client,
            collection_name=self.collection_name,
            embeddings=self.embeddings,
        )
        
        # Create retriever
        logger.info(f"Creating retriever with k={self.top_k}")
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": self.top_k}
        )
        
        logger.info("QdrantRetriever initialized successfully")
    
    def retrieve_documents(self, query):
        """Retrieve relevant documents from Qdrant based on the query."""
        logger.info(f"Retrieving documents for query: '{query}'")
        
        try:
            docs = self.retriever.get_relevant_documents(query)
            logger.info(f"Retrieved {len(docs)} documents from Qdrant")
            return docs
        except Exception as e:
            logger.error(f"Error retrieving documents from Qdrant: {str(e)}")
            raise
    
    def extract_context(self, docs):
        """Extract content from retrieved documents and filter by relevance."""
        logger.info(f"Extracting context from {len(docs)} documents")
        
        context = []
        for i, doc in enumerate(docs):
            try:
                # Log metadata keys without logging potentially large values
                metadata_keys = list(doc.metadata.keys()) if hasattr(doc, 'metadata') else []
                content_length = len(doc.page_content) if hasattr(doc, 'page_content') else 0
                
                # Calculate a simple relevance score using metadata if available
                relevance_score = 1.0  # Default score
                if hasattr(doc, 'metadata') and 'score' in doc.metadata:
                    relevance_score = float(doc.metadata.get('score', 1.0))
                    
                logger.info(f"Document {i+1}: metadata keys: {metadata_keys}, content length: {content_length}, relevance: {relevance_score:.4f}")
                
                # Filter out content with very low relevance
                if relevance_score < 0.5:
                    logger.info(f"Skipping document {i+1} due to low relevance score: {relevance_score:.4f}")
                    continue
                
                context_item = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "relevance": relevance_score
                }
                
                context.append(context_item)
            except Exception as e:
                logger.error(f"Error extracting context from document {i+1}: {str(e)}")
        
        # Sort context by relevance score (highest first)
        context.sort(key=lambda x: x.get('relevance', 0), reverse=True)
        
        logger.info(f"Extracted context from {len(context)} documents after relevance filtering")
        return context
    
    def get_context_for_query(self, query):
        """Get context from Qdrant for a specific query."""
        logger.info(f"Getting context for query: '{query}'")
        
        docs = self.retrieve_documents(query)
        context = self.extract_context(docs)
        return context
    
    def generate_questions(self, query):
        """Generate related questions based on the input query."""
        logger.info(f"Generating related questions for query: '{query}'")
        
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7
        )
        
        prompt = f"""
        Based on this user query: "{query}"
        
        Generate 3-4 highly specific questions that would help retrieve the most relevant information 
        from a knowledge base about Sergey Chernenko's views on this topic.
        
        Focus on questions that target different aspects of the topic to get diverse but relevant information.
        Make questions very specific and targeted, not general.
        
        Format: Return just the questions, one per line.
        """
        
        logger.info("Sending prompt to LLM to generate questions")
        try:
            response = llm.invoke(prompt)
            questions = [q.strip() for q in response.content.strip().split('\n') if q.strip()]
            logger.info(f"Generated {len(questions)} related questions: {questions}")
            return questions
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            # Return at least one question (the original) in case of error
            logger.info("Returning original query as fallback")
            return [query] 