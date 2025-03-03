# Social Media Content Generator Bot

A Telegram bot that helps create optimized content for different social media platforms.

## Features

- Accepts Google Doc links as input
- Splits content into manageable parts
- Supports multiple social media platforms:
  - Dzen.ru
  - VKontakte
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