# exa_search_tool.py
import os
import logging
import traceback
from typing import Any, List
from pydantic import Field
from dotenv import load_dotenv
from exa_py import Exa
from langchain.agents import tool
from crewai.tools import BaseTool as CrewaiBaseTool

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Define tool classes
class ExaSearchTool(CrewaiBaseTool):
    """Tool for searching the web using Exa."""
    
    name: str = "exa_search"
    description: str = "Search the web for information related to a query using Exa search engine."
    # Properly define toolset as a field
    exa_toolset: Any = Field(description="Exa search toolset instance")
    
    def schema(self) -> dict:
        base_schema = super().schema()
        base_schema["properties"] = {
            "query": {"type": "string", "description": "The query to search for on the web"},
            "description": {"type": "string", "description": "Alternative field for query"}
        }
        # Make it more flexible - only require one of the fields
        base_schema["required"] = []
        return base_schema
    
    def _run(self, query: str = None, **kwargs) -> str:
        """Run the tool with the given query."""
        logger.info(f"Running exa_search tool with input type: {type(query)}")
        
        # For CrewAI tools, the input might be in the first unnamed parameter
        if not query and not kwargs and len(self._run.__code__.co_varnames) > 1:
            # Try to get the first argument value
            import inspect
            frame = inspect.currentframe()
            try:
                if frame and frame.f_back:
                    arg_values = inspect.getargvalues(frame.f_back)
                    if 'args' in arg_values.locals and arg_values.locals['args']:
                        # Handle the case where the first argument might be the query
                        first_arg = arg_values.locals['args'][1] if len(arg_values.locals['args']) > 1 else None
                        if first_arg:
                            logger.info(f"Found query in first argument: {first_arg}")
                            query = first_arg
            finally:
                del frame  # Avoid reference cycles
        
        # If still no query, check kwargs
        if not query and kwargs:
            query = kwargs.get('query') or kwargs.get('description', '')
        
        logger.info(f"Running exa_search tool with query: {query[:50] if query else 'empty'}...")
        logger.info(f"Query type: {type(query)}, Value: {query}")
        
        # Handle if query is a JSON string
        if isinstance(query, str) and (query.startswith('{') and query.endswith('}')):
            try:
                import json
                parsed_json = json.loads(query)
                logger.info(f"Parsed JSON string to dict: {parsed_json}")
                if isinstance(parsed_json, dict):
                    if 'query' in parsed_json:
                        query = parsed_json['query']
                        logger.info(f"Extracted query from JSON string: {query[:50] if query else 'empty'}")
                    elif 'description' in parsed_json:
                        query = parsed_json['description']
                        logger.info(f"Extracted description from JSON string: {query[:50] if query else 'empty'}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse query as JSON: {e}")
        
        # Handle if query is a dict instead of a string
        if isinstance(query, dict):
            logger.info(f"Query is a dict with keys: {query.keys()}")
            if 'query' in query:
                query = query['query']
                logger.info(f"Extracted string query from dict: {query[:50] if query else 'empty'}")
            elif 'description' in query:
                query = query['description']
                logger.info(f"Extracted description from dict: {query[:50] if query else 'empty'}")
            else:
                logger.warning(f"Query dict does not contain 'query' or 'description' keys: {query}")
        
        logger.info(f"Final query after processing: {query[:100] if query else 'empty'}")
        
        # Prevent empty queries
        if not query or (isinstance(query, str) and query.strip() == ''):
            logger.warning("Empty query received in exa_search")
            return "No query provided. Please provide a specific question or topic to search for."
        
        try:
            results = self.exa_toolset.search(query)
            logger.info(f"Exa search succeeded with {len(results.results) if hasattr(results, 'results') else 0} results")
            
            # Format the results in a readable way
            formatted_results = []
            for i, result in enumerate(results.results):
                try:
                    summary = result.text[:150] + "..." if result.text else "No text available"
                    formatted_results.append(f"{i+1}. {result.title}\n   URL: {result.url}\n   ID: {result.id}\n   Summary: {summary}\n")
                except (AttributeError, TypeError) as e:
                    # Handle case where result attributes might be missing
                    logger.warning(f"Error formatting result {i}: {str(e)}")
                    formatted_results.append(f"{i+1}. [Could not format result properly]\n   URL: {getattr(result, 'url', 'Unknown URL')}\n")
            
            if formatted_results:
                return "Found the following results:\n\n" + "\n".join(formatted_results)
            else:
                return "No results found for your query."
                
        except Exception as e:
            logger.error(f"Error in exa_search tool: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error searching the web: {str(e)}"

class ExaFindSimilarTool(CrewaiBaseTool):
    """Tool for finding similar webpages using Exa."""
    
    name: str = "exa_find_similar"
    description: str = "Find webpages similar to a given URL using Exa."
    # Properly define toolset as a field
    exa_toolset: Any = Field(description="Exa search toolset instance")
    
    def schema(self) -> dict:
        base_schema = super().schema()
        base_schema["properties"] = {
            "url": {"type": "string", "description": "The URL to find similar pages for"}
        }
        base_schema["required"] = ["url"]
        return base_schema
    
    def _run(self, url: str) -> str:
        """Run the tool with the given URL."""
        logger.info(f"Running exa_find_similar tool with URL: {url[:50] if url else 'empty'}...")
        
        # Prevent empty URLs
        if not url or (isinstance(url, str) and url.strip() == ''):
            logger.warning("Empty URL received in exa_find_similar")
            return "No URL provided. Please provide a valid URL to find similar pages."
        
        try:
            results = self.exa_toolset.find_similar(url)
            logger.info(f"Exa find_similar succeeded with {len(results.results) if hasattr(results, 'results') else 0} results")
            
            # Format the results in a readable way
            formatted_results = []
            for i, result in enumerate(results.results):
                try:
                    summary = result.text[:150] + "..." if result.text else "No text available"
                    formatted_results.append(f"{i+1}. {result.title}\n   URL: {result.url}\n   ID: {result.id}\n   Summary: {summary}\n")
                except (AttributeError, TypeError) as e:
                    # Handle case where result attributes might be missing
                    logger.warning(f"Error formatting result {i}: {str(e)}")
                    formatted_results.append(f"{i+1}. [Could not format result properly]\n   URL: {getattr(result, 'url', 'Unknown URL')}\n")
            
            if formatted_results:
                return "Found the following similar pages:\n\n" + "\n".join(formatted_results)
            else:
                return "No similar pages found for the provided URL."
                
        except Exception as e:
            logger.error(f"Error in exa_find_similar tool: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error finding similar pages: {str(e)}"

class ExaGetContentsTool(CrewaiBaseTool):
    """Tool for getting the contents of webpages using Exa."""
    
    name: str = "exa_get_contents"
    description: str = "Get the contents of webpages identified by their IDs from previous search results."
    # Properly define toolset as a field
    exa_toolset: Any = Field(description="Exa search toolset instance")
    
    def schema(self) -> dict:
        base_schema = super().schema()
        base_schema["properties"] = {
            "ids": {"type": "string", "description": "The list of IDs to retrieve content for, in the format of a string representation of a list (e.g., \"['id1', 'id2']\""}
        }
        base_schema["required"] = ["ids"]
        return base_schema
    
    def _run(self, ids: str) -> str:
        """Run the tool with the given IDs."""
        logger.info(f"Running exa_get_contents tool with IDs: {ids[:50] if ids else 'empty'}...")
        
        # Prevent empty IDs
        if not ids or (isinstance(ids, str) and ids.strip() == ''):
            logger.warning("Empty IDs received in exa_get_contents")
            return "No IDs provided. Please provide valid IDs to get contents."
        
        try:
            # Safely evaluate the string representation of the list
            try:
                id_list = eval(ids)
                if not isinstance(id_list, list):
                    id_list = [ids]  # If it's not a list after eval, treat the input as a single ID
            except:
                # If eval fails, assume it's a single ID
                id_list = [ids]
            
            contents = self.exa_toolset.get_contents(id_list)
            logger.info(f"Exa get_contents succeeded")
            
            # Format the contents
            formatted_contents = []
            for content in contents:
                excerpt = f"Title: {content.title}\nURL: {content.url}\nContent: {content.text[:1000]}..."
                formatted_contents.append(excerpt)
            
            if formatted_contents:
                return "Retrieved the following contents:\n\n" + "\n\n---\n\n".join(formatted_contents)
            else:
                return "No content found for the provided IDs."
                
        except Exception as e:
            logger.error(f"Error in exa_get_contents tool: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error getting contents: {str(e)}"

class ExaSearchToolset:
    """Tools for searching the web using Exa."""
    
    # Define priority websites for searches
    PRIORITY_WEBSITES = [
        "https://dzen.ru/id/6235c18dbb7c5c3f01f9adde",
        "https://sergeichernenko.ru/"
    ]
    
    def __init__(self):
        """Initialize the Exa client."""
        logger.info("Initializing ExaSearchToolset")
        try:
            # Get API key
            api_key = os.getenv("EXA_API_KEY")
            if not api_key:
                logger.error("EXA_API_KEY not found in environment variables")
                raise ValueError("EXA_API_KEY is required but not found in environment variables")
            
            # Initialize Exa client
            self.client = Exa(api_key=api_key)
            logger.info("ExaSearchToolset initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Exa search: {str(e)}")
            logger.error(traceback.format_exc())
            self.client = None
            logger.warning("Using fallback null implementation for Exa search")
    
    def search(self, query, num_results=3):
        """Search for webpages based on the query."""
        logger.info(f"Direct search called with: {query[:50] if query else 'empty'}...")
        try:
            if not self.client:
                logger.warning("Exa client is not available")
                return "Exa search is not available."
            
            # Try searching priority websites first
            priority_results = []
            for website in self.PRIORITY_WEBSITES:
                try:
                    # Use site: prefix to search within specific website
                    site_query = f"site:{website} {query}"
                    logger.info(f"Searching priority website with query: {site_query[:50]}...")
                    site_results = self.client.search(site_query, use_autoprompt=True, num_results=num_results)
                    
                    if hasattr(site_results, 'results') and site_results.results:
                        logger.info(f"Found {len(site_results.results)} results from priority website: {website}")
                        priority_results.extend(site_results.results)
                except Exception as site_e:
                    logger.warning(f"Error searching priority website {website}: {str(site_e)}")
            
            # If we have enough results from priority websites, return those
            if len(priority_results) >= num_results:
                logger.info(f"Returning {num_results} results from priority websites")
                # Create a new results object with just the priority results
                from types import SimpleNamespace
                results = SimpleNamespace()
                results.results = priority_results[:num_results]
                return results
            
            # Otherwise, perform a general search
            logger.info("Performing general search...")
            general_results = self.client.search(query, use_autoprompt=True, num_results=max(1, num_results - len(priority_results)))
            
            # Combine priority results with general results if needed
            if priority_results and hasattr(general_results, 'results'):
                from types import SimpleNamespace
                combined_results = SimpleNamespace()
                combined_results.results = priority_results + general_results.results
                combined_results.results = combined_results.results[:num_results]
                logger.info(f"Returning combined results: {len(combined_results.results)} total")
                return combined_results
            
            # Otherwise just return general results
            logger.info("Returning general search results")
            return general_results
        
        except Exception as e:
            logger.error(f"Error searching with Exa: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error searching the web: {str(e)}"
    
    def find_similar(self, url, num_results=3):
        """Find similar webpages to the given URL."""
        logger.info(f"Direct find_similar called with URL: {url[:50] if url else 'empty'}...")
        try:
            if not self.client:
                logger.warning("Exa client is not available")
                return "Exa search is not available."
            
            return self.client.find_similar(url, num_results=num_results)
        
        except Exception as e:
            logger.error(f"Error finding similar pages with Exa: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error finding similar pages: {str(e)}"
    
    def get_contents(self, ids):
        """Get the contents of webpages by their IDs."""
        id_str = str(ids)[:50] + "..." if len(str(ids)) > 50 else str(ids)
        logger.info(f"Direct get_contents called with IDs: {id_str}...")
        try:
            if not self.client:
                logger.warning("Exa client is not available")
                return "Exa search is not available."
            
            return self.client.get_contents(ids)
        
        except Exception as e:
            logger.error(f"Error getting contents with Exa: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error getting webpage contents: {str(e)}"
    
    def tools(self):
        """Return properly formatted tools for CrewAI"""
        # Create CrewAI compatible tools
        logger.info("Creating CrewAI tools for Exa search")
        try:
            tools = [
                ExaSearchTool(exa_toolset=self),
                ExaFindSimilarTool(exa_toolset=self),
                ExaGetContentsTool(exa_toolset=self),
                DirectUrlContentTool(exa_toolset=self)
            ]
            logger.info(f"Successfully created {len(tools)} CrewAI tools for Exa search")
            return tools
        except Exception as e:
            logger.error(f"Error creating CrewAI tools for Exa search: {str(e)}")
            logger.error(traceback.format_exc())
            logger.warning("Returning empty tools list as fallback")
            return []

    def get_url_content(self, url):
        """Get the content of a specific URL directly."""
        logger.info(f"Retrieving content directly from URL: {url[:50] if url else 'empty'}...")
        try:
            if not self.client:
                logger.warning("Exa client is not available")
                return "Exa client is not available."
            
            # To get content from a URL, we need to search for it first to get the ID
            site_query = f"url:{url}"
            logger.info(f"Searching for URL with query: {site_query}")
            search_results = self.client.search(site_query, use_autoprompt=False, num_results=1)
            
            if not hasattr(search_results, 'results') or not search_results.results:
                logger.warning(f"No search results found for URL: {url}")
                # Try an alternative approach - use text extraction directly
                contents = self.client.get_text_contents_from_url(url)
                if contents:
                    logger.info(f"Successfully retrieved content directly from URL: {url}")
                    from types import SimpleNamespace
                    content = SimpleNamespace()
                    content.title = "Extracted content"
                    content.url = url
                    content.text = contents
                    return [content]
                return []
            
            # Get the document ID from the search result
            doc_id = search_results.results[0].id
            logger.info(f"Found document ID: {doc_id} for URL: {url}")
            
            # Get the content using the document ID
            contents = self.client.get_contents([doc_id])
            logger.info(f"Successfully retrieved content for URL: {url}")
            
            return contents
            
        except Exception as e:
            logger.error(f"Error retrieving content from URL {url}: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error retrieving content: {str(e)}"

class DirectUrlContentTool(CrewaiBaseTool):
    """Tool for directly retrieving content from specific URLs."""
    
    name: str = "exa_url_content"
    description: str = "Directly retrieve content from a specific URL."
    # Properly define toolset as a field
    exa_toolset: Any = Field(description="Exa search toolset instance")
    
    def schema(self) -> dict:
        base_schema = super().schema()
        base_schema["properties"] = {
            "url": {"type": "string", "description": "The URL to retrieve content from"}
        }
        base_schema["required"] = ["url"]
        return base_schema
    
    def _run(self, url: str) -> str:
        """Run the tool with the given URL."""
        logger.info(f"Running exa_url_content tool with URL: {url[:50] if url else 'empty'}...")
        
        # Prevent empty URLs
        if not url or (isinstance(url, str) and url.strip() == ''):
            logger.warning("Empty URL received in exa_url_content")
            return "No URL provided. Please provide a valid URL to retrieve content."
        
        try:
            contents = self.exa_toolset.get_url_content(url)
            
            # Format the contents
            if isinstance(contents, list) and contents:
                formatted_contents = []
                for content in contents:
                    excerpt = f"Title: {content.title if hasattr(content, 'title') else 'No title'}\nURL: {content.url if hasattr(content, 'url') else url}\nContent: {content.text[:2000] if hasattr(content, 'text') else 'No content'}..."
                    formatted_contents.append(excerpt)
                
                if formatted_contents:
                    return "Retrieved the following content:\n\n" + "\n\n---\n\n".join(formatted_contents)
            
            return "No content could be retrieved from the provided URL."
                
        except Exception as e:
            logger.error(f"Error in exa_url_content tool: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error retrieving content: {str(e)}" 