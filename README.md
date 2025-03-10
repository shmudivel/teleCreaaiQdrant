# Social Media Content Generator Bot

A Telegram bot that helps create optimized content for different social media platforms.

## Features

- Accepts Google Doc links as input
- Splits content into manageable parts
- Supports multiple social media platforms:
  - Dzen.ru
  - VC.ru
- Uses AI agents to optimize content for each platform
- Performs SEO optimization
- Saves results to Google Drive

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env` file:
   ```
   TELEGRAM_TOKEN=your_telegram_bot_token
   OPENAI_API_KEY=your_openai_api_key
   QDRANT_URL=http://qdrant:6333
   ```
4. Place your Google service account JSON file in the project root

## Running the Bot

### Development 

## Adding New Platforms

To add support for a new social media platform:

1. Create a new folder in `src/platforms/` for your platform
2. Implement the required classes:
   - `agents.py` - Define platform-specific agents
   - `tasks.py` - Define platform-specific tasks
3. Update the `PlatformFactory` class in `src/platforms/factory.py` to include your new platform

## License

MIT 

## Content Quality Improvements

We've made several improvements to the content generation system to address quality issues:

### 1. Enhanced Task Instructions

- Added explicit instructions to preserve the author's name (Сергей Черненко)
- Created specific guidelines for proper paragraph structure
- Added requirements for accurate statistics and financial data representation
- Included instructions to avoid made-up terminology
- Added guidance for proper explanation of complex concepts

### 2. Updated Agent Implementations

- Added ACCURACY_GUIDELINES to ensure precise factual representation
- Added STRUCTURE_GUIDELINES to enforce proper paragraph and sentence structure
- Improved style guide generation to better capture the original author's voice
- Added explicit instructions to include author's name in all content

### 3. Content Quality Verification

- Added a ContentReviewer class to automatically check for common issues:
  - Missing or placeholder author names
  - Single-word sentences
  - Awkward or made-up phrases
  - Incorrect terminology usage
  - Short paragraphs
  - Statistics presented without context

- Implemented automatic fixing for common issues:
  - Replacing name placeholders with the correct author name
  - Fixing incorrect terminology

- Added quality reporting:
  - Summary report showing all issues found
  - Detailed report with specific problematic sections
  
- Integrated quality checking into the content generation pipeline

These improvements help ensure that generated content maintains the original author's style, uses correct terminology, presents statistics accurately, and follows proper formatting standards. 