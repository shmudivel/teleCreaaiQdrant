import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from langchain_qdrant import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
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
        self.qdrant_url = os.getenv("QDRANT_HOST", os.getenv("QDRANT_URL", "http://qdrant:6333"))
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = collection_name
        self.top_k = top_k
        
        logger.info(f"Connecting to Qdrant at {self.qdrant_url}, collection: {self.collection_name}")
        
        try:
            # Initialize client
            self.client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key
            )
            
            # Check if collection exists and create it if needed
            self._ensure_collection_exists()
            
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
            
            # Initialize LLM
            logger.info("Initializing Claude 3.7 Sonnet model")
            self.llm = ChatAnthropic(
                model_name="claude-3-5-sonnet-20240620",
                temperature=0.7,
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
            )
            
            logger.info("QdrantRetriever initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing QdrantRetriever: {str(e)}")
            raise
    
    def _ensure_collection_exists(self):
        """Check if collection exists and create it if needed."""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [collection.name for collection in collections]
            
            if self.collection_name not in collection_names:
                logger.warning(f"Collection '{self.collection_name}' not found. Creating it...")
                
                # Create new collection with OpenAI embedding dimension (1536 for text-embedding-3-small)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=rest.VectorParams(
                        size=1536,  # OpenAI embedding dimension
                        distance=rest.Distance.COSINE
                    )
                )
                logger.info(f"Collection '{self.collection_name}' created successfully")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")
                
        except Exception as e:
            logger.error(f"Error checking/creating collection: {str(e)}")
            raise
    
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
    
    def extract_keywords(self, query):
        """Extract important keywords from the query using LLM."""
        logger.info(f"Extracting keywords from query: '{query}'")
        
        prompt = f"""
        Extract 3-5 search-optimized keywords from this query: "{query}"

        Priority order:
        - Technical/domain terminology
        - Named entities (people, products, organizations)
        - Core concepts or specific problems

        Return only comma-separated keywords without explanation or additional text.
        Example: "blockchain, smart contracts, decentralized finance
        """
        
        try:
            response = self.llm.invoke(prompt)
            keywords = [k.strip() for k in response.content.strip().split(',') if k.strip()]
            logger.info(f"Extracted keywords: {keywords}")
            return keywords
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            # Return query as a fallback
            return [query]
    
    def generate_questions_from_keywords(self, keywords, original_query):
        """Generate targeted questions based on extracted keywords."""
        logger.info(f"Generating questions from keywords: {keywords}")
        
        keywords_text = ", ".join(keywords)
        prompt = f"""
        Based on this user query: "{original_query}"
        
        And focusing on these key concepts: {keywords_text}
        
        Generate 3-4 highly specific questions that would help retrieve the most relevant information 
        from a knowledge base about Sergey Chernenko's views on these topics.
        
        Each question should focus on one or more of the key concepts to get diverse but relevant information.
        Make questions very specific and targeted, not general.
        
        Format: Return just the questions, one per line.
        """
        
        logger.info("Sending prompt to LLM to generate targeted questions")
        try:
            response = self.llm.invoke(prompt)
            questions = [q.strip() for q in response.content.strip().split('\n') if q.strip()]
            logger.info(f"Generated {len(questions)} targeted questions: {questions}")
            return questions
        except Exception as e:
            logger.error(f"Error generating questions from keywords: {str(e)}")
            # Return keywords as questions for fallback
            return [f"What does Sergey think about {k}?" for k in keywords]
    
    def get_enhanced_context_for_query(self, query):
        """Get enhanced context using keyword extraction and targeted questions."""
        logger.info(f"Getting enhanced context for query: '{query}'")
        
        # Step 1: Extract keywords from the query
        keywords = self.extract_keywords(query)
        
        # Step 2: Generate targeted questions based on keywords
        questions = self.generate_questions_from_keywords(keywords, query)
        
        # Step 3: Collect context from original query, keywords, and questions
        all_contexts = []
        
        # Get context for original query
        logger.info("Retrieving context for original query...")
        original_context = self.get_context_for_query(query)
        all_contexts.extend(original_context)
        
        # Get context for each keyword
        for keyword in keywords:
            logger.info(f"Retrieving context for keyword: '{keyword}'")
            keyword_context = self.get_context_for_query(keyword)
            all_contexts.extend(keyword_context)
        
        # Get context for each targeted question
        max_questions = 3  # Limit the number of questions to prevent context overload
        for i, question in enumerate(questions[:max_questions]):
            logger.info(f"Retrieving context for targeted question {i+1}: '{question}'")
            question_context = self.get_context_for_query(question)
            all_contexts.extend(question_context)
        
        # Step 4: Deduplicate and sort by relevance
        deduplicated_context = self._deduplicate_context(all_contexts)
        
        logger.info(f"Enhanced context retrieval complete with {len(deduplicated_context)} unique items")
        return deduplicated_context
    
    def _deduplicate_context(self, contexts):
        """Deduplicate context items by content and sort by relevance."""
        seen_contents = set()
        unique_contexts = []
        
        for ctx in contexts:
            content = ctx.get("content", "")
            # Use a short content hash to check for duplicates
            content_hash = hash(content[:100])
            
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_contexts.append(ctx)
        
        # Sort by relevance (highest first)
        unique_contexts.sort(key=lambda x: x.get('relevance', 0), reverse=True)
        return unique_contexts
    
    def generate_questions(self, query):
        """Generate related questions based on the input query."""
        logger.info(f"Generating related questions for query: '{query}'")
        
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
            response = self.llm.invoke(prompt)
            questions = [q.strip() for q in response.content.strip().split('\n') if q.strip()]
            logger.info(f"Generated {len(questions)} related questions: {questions}")
            return questions
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            # Return at least one question (the original) in case of error
            logger.info("Returning original query as fallback")
            return [query]
    
    def test_enhanced_retrieval(self, query):
        """
        Test method to demonstrate the enhanced retrieval process.
        Shows each step of keyword extraction, question generation, and searching.
        
        Args:
            query (str): The test query to process
            
        Returns:
            dict: Results from each step of the process
        """
        results = {
            "original_query": query,
            "steps": []
        }
        
        # Step 1: Extract keywords
        keywords = self.extract_keywords(query)
        results["steps"].append({
            "step": "keyword_extraction",
            "keywords": keywords
        })
        
        # Step 2: Generate questions from keywords
        questions = self.generate_questions_from_keywords(keywords, query)
        results["steps"].append({
            "step": "question_generation",
            "questions": questions
        })
        
        # Step 3: Get context for original query
        original_context = self.get_context_for_query(query)
        results["steps"].append({
            "step": "original_query_search",
            "context_count": len(original_context),
            "sample": original_context[:1] if original_context else []
        })
        
        # Step 4: Get context for each keyword
        keyword_results = []
        for keyword in keywords:
            keyword_context = self.get_context_for_query(keyword)
            keyword_results.append({
                "keyword": keyword,
                "context_count": len(keyword_context),
                "sample": keyword_context[:1] if keyword_context else []
            })
        results["steps"].append({
            "step": "keyword_search",
            "results": keyword_results
        })
        
        # Step 5: Get context for targeted questions
        question_results = []
        for question in questions[:2]:  # Limit to first 2 questions
            question_context = self.get_context_for_query(question)
            question_results.append({
                "question": question,
                "context_count": len(question_context),
                "sample": question_context[:1] if question_context else []
            })
        results["steps"].append({
            "step": "question_search",
            "results": question_results
        })
        
        # Step 6: Final enhanced context
        enhanced_context = self.get_enhanced_context_for_query(query)
        results["final_context_count"] = len(enhanced_context)
        
        return results 