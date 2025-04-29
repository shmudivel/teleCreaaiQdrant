"""
API utilities for handling API calls with proper retry logic, backoff, and rate limiting.
This module helps to handle API rate limits and temporary failures gracefully.
"""

import time
import random
import logging
import functools
from typing import Callable, Any, TypeVar
import anthropic

# Set up logging
logger = logging.getLogger(__name__)

# Type variable for function return type
T = TypeVar('T')

# Constants for retry settings
MAX_RETRIES = 5
BASE_DELAY = 1.0  # Base delay in seconds
MAX_DELAY = 60.0  # Maximum delay
RATE_LIMIT_DELAY = 20.0  # Delay when rate limited
JITTER_FACTOR = 0.1  # Random jitter factor (10%)

def exponential_backoff_retry(
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_DELAY,
    max_delay: float = MAX_DELAY,
    jitter_factor: float = JITTER_FACTOR
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for adding exponential backoff retry logic to API calls.
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries
        jitter_factor: Random jitter factor to add to delay
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            retry_count = 0
            delay = base_delay
            
            while True:
                try:
                    return func(*args, **kwargs)
                except anthropic.RateLimitError as e:
                    retry_count += 1
                    if retry_count > max_retries:
                        logger.error(f"Rate limit exceeded after {max_retries} retries: {str(e)}")
                        raise
                    
                    # Use longer delay for rate limits
                    sleep_time = RATE_LIMIT_DELAY
                    logger.warning(
                        f"Rate limit hit (retry {retry_count}/{max_retries}). "
                        f"Waiting {sleep_time:.2f}s before retrying..."
                    )
                    time.sleep(sleep_time)
                
                except anthropic.APIStatusError as e:
                    # Handle 529 Overloaded and other API errors
                    retry_count += 1
                    if retry_count > max_retries:
                        logger.error(f"API Error after {max_retries} retries: {str(e)}")
                        raise
                    
                    # Add jitter to delay (±10%)
                    jitter = random.uniform(-jitter_factor * delay, jitter_factor * delay)
                    sleep_time = min(delay + jitter, max_delay)
                    
                    logger.warning(
                        f"API Error: {e.status_code} - {str(e)} (retry {retry_count}/{max_retries}). "
                        f"Waiting {sleep_time:.2f}s before retrying..."
                    )
                    time.sleep(sleep_time)
                    
                    # Exponential backoff
                    delay = min(delay * 2, max_delay)
                
                except Exception as e:
                    # Handle other exceptions - no retry
                    logger.error(f"Unexpected error: {str(e)}")
                    raise
        
        return wrapper
    
    return decorator

def create_claude_client(api_key: str) -> anthropic.Anthropic:
    """
    Create an Anthropic client with appropriate settings.
    
    Args:
        api_key: Anthropic API key
        
    Returns:
        Configured Anthropic client
    """
    # The current client doesn't have rate limiting settings in its constructor
    # In the future, we might set additional settings here
    return anthropic.Anthropic(api_key=api_key)

@exponential_backoff_retry()
def call_claude_api(client, model, prompt, system=None, max_tokens=1000, temperature=0.0) -> str:
    """
    Call the Claude API with retry logic.
    
    Args:
        client: Anthropic client
        model: Model name
        prompt: User prompt
        system: System prompt
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        
    Returns:
        Generated text response
    """
    messages = [{"role": "user", "content": prompt}]
    
    response = client.messages.create(
        model=model,
        messages=messages,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    # Extract text from response
    result = ""
    if hasattr(response.content, '__iter__') and not isinstance(response.content, str):
        for item in response.content:
            if hasattr(item, 'text') and item.text:
                result += item.text
    else:
        result = str(response.content)
    
    return result

# Rate limiting context manager to avoid hitting API limits
class RateLimiter:
    """Context manager for rate limiting API calls."""
    
    def __init__(self, calls_per_minute: int = 12):
        """
        Initialize the rate limiter.
        
        Args:
            calls_per_minute: Maximum calls per minute
        """
        self.min_seconds_between_calls = 60.0 / calls_per_minute
        self.last_call_time = 0
    
    def __enter__(self):
        """Enter the context and enforce rate limiting."""
        now = time.time()
        time_since_last_call = now - self.last_call_time
        
        if time_since_last_call < self.min_seconds_between_calls:
            sleep_time = self.min_seconds_between_calls - time_since_last_call
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_call_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        pass 