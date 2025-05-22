# Workflow System - Content to Reels

This module contains a complete workflow for transforming a Google Doc document into multiple short-form video reels optimized for social media engagement.

## Workflow Overview

1. **Document Analysis** - Extracts content from a Google Doc and divides it into topical sections
2. **Reel Script Generation** - Converts each section into an engaging Instagram reel script 
3. **Viral Potential Analysis** - Analyzes each script for viral potential and selects the top ones
4. **Final Reel Editing** - Applies engagement improvements with hooks and narrative structure
5. **Script Validation** - Validates scripts to ensure they comply with requirements
6. **Number Conversion** - Converts numbers to words for better voice delivery
7. **HeyGen Script Optimization** - Optimizes scripts for natural delivery by the AI avatar (adds SSML tags)
8. **Video Generation** - Creates videos using the HeyGen API with an AI avatar
9. **Publishing** - Uploads videos to Google Drive and/or YouTube

## File Structure

- `integration.py` - Main orchestration file that combines all workflow steps
- `analyze_google_doc.py` - Extracts and analyzes content from Google Docs
- `create_reel_scripts.py` - Transforms sections into reel scripts
- `reel_picker.py` - Identifies reels with highest viral potential
- `prompts.py` - Centralized file containing all prompts used in the workflow
- `tasks.py` - Task definitions for background/scheduled execution
- `agents.py` - Agent definitions (future extension)
- `path_setup.py` - Utility for path configuration
- `api_utils.py` - Utilities for API calls with rate limiting and retries

## Prompts Organization

All prompts used in the workflow are centralized in `prompts.py` and follow this sequence:

1. **DOC_ANALYSIS_PROMPT** - Used in `analyze_google_doc.py` to divide document into sections
2. **REEL_GENERATION_PROMPT** - Used in `create_reel_scripts.py` to create reel scripts
3. **VIRAL_ANALYSIS_PROMPT** - Used in `reel_picker.py` to score viral potential
4. **FINAL_EDITING_PROMPT** - Used in `integration.py` to apply final engagement improvements
5. **DEFAULT_EDIT_GUIDELINES** - Rules for improving reel engagement
6. **HOOK_VARIATIONS** - Different hook styles to use in final editing
7. **SCRIPT_VALIDATION_PROMPT** - Used in `integration.py` to validate and fix scripts for HeyGen
8. **NUMBER_CONVERSION_PROMPT** - Used in `integration.py` to convert numbers to their word representation
9. **HEYGEN_OPTIMIZATION_PROMPT** - Used in `integration.py` to optimize scripts for natural voice delivery

This centralized organization makes it easy to modify the prompts without changing multiple files.

## API Resilience

The workflow is designed with robust API resilience features to handle rate limits and API errors:

- **Exponential Backoff** - Automatically retries failed API calls with increasing wait times
- **Rate Limiting** - Prevents hitting API rate limits by spacing out requests
- **Error Handling** - Gracefully handles API errors like 429 (rate limit) and 529 (overloaded)
- **Jittered Retries** - Adds randomized jitter to retry timing to prevent thundering herd problems

The `api_utils.py` file provides utilities that make the workflow robust against common API issues:

- `exponential_backoff_retry()` - Decorator for automatic retries with exponential backoff
- `call_claude_api()` - Resilient function for making Claude API calls with proper error handling
- `RateLimiter` - Context manager to enforce API rate limits
- `create_claude_client()` - Factory function for creating properly configured API clients

## Usage

The main entry point is the `process_google_doc_to_reels` function in `integration.py`:

```python
from src.platforms.workflow.integration import process_google_doc_to_reels

# Process a Google Doc and create reels
results = process_google_doc_to_reels(
    doc_url="https://docs.google.com/document/d/YOUR_DOC_ID/edit",
    output_dir="output_folder",
    top_n=10  # Number of top reels to select
)

# Access generated files
analyzed_doc_path = results["analyzed_doc"]
final_reels_dir = results["final_reels_dir"]
optimized_dir = results["optimized_dir"]
```

## Environment Requirements

The workflow requires the following environment variables:

- `GOOGLE_SERVICE_ACCOUNT_PATH` - Path to Google service account credentials
- `ANTHROPIC_API_KEY` - API key for Claude AI model
- `HEYGEN_API_KEY` - API key for HeyGen video generation
- `YOUTUBE_CLIENT_ID` and `YOUTUBE_CLIENT_SECRET` - For YouTube uploads 