# Telegram Bot Fixes

## Issues Fixed

### 1. "Обновить Google Sheet" Button Not Working
**Problem**: The "Обновить Google Sheet" button was present in the main menu but clicking it didn't trigger any action.

**Fix**:
- Added a callback handler for the "menu_update_sheet" pattern in the main application handlers
- Also added the same handler in the conversation fallbacks to ensure it works during active conversations
- Code changes:
```python
# Added to main application handlers
application.add_handler(CallbackQueryHandler(handle_menu_selection, pattern="^menu_update_sheet$|^menu_text_post$|^menu_vector_db$"))

# Added to conversation fallbacks
fallbacks=[
    # ... existing fallbacks
    CallbackQueryHandler(handle_menu_selection, pattern="^menu_update_sheet$|^menu_text_post$|^menu_vector_db$"),
    # ... other fallbacks
]
```

### 2. `/start` Command Not Properly Resetting State
**Problem**: When a user sent the `/start` command, it didn't properly reset all conversation states.

**Fix**:
- Improved the `start` function to clear user data and log the action
- Registered important command handlers with higher priority (group=0) to ensure they interrupt any active conversation
- Code changes:
```python
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get user ID for logging
    user_id = update.effective_user.id
    logger.info(f"User {user_id} is starting a new session with /start command")
    
    # Clear user data to start fresh
    context.user_data.clear()
    
    # Send welcome message and show menu
    # ...
    
    # Log the start command
    asyncio.create_task(log_message_to_sheet(user_id, "/start (command)", "", True))
    
    # End any active conversation
    return ConversationHandler.END
```

```python
# Add high-priority command handlers first
application.add_handler(CommandHandler("start", start), group=0)
application.add_handler(CommandHandler("restart", restart_command), group=0)
# ... other command handlers
```

## Remaining Issues

### 1. "Создать текстовый пост" Button Not Working
**Problem**: The "Создать текстовый пост" button in the main menu doesn't trigger any action.

**Potential causes**:
- The button uses "menu_text_post" as its callback_data, which should be handled by the same handle_menu_selection function
- If accessing the Google API for text post creation is failing, it might stop with an error
- There could be an issue with the text processing or platform selection

**Troubleshooting steps**:
- Add more logging in the handle_menu_selection function specifically for the "menu_text_post" case
- Check Google API credentials and permissions for reading Google Docs
- Verify the handler is properly registered both in the main application and conversation fallbacks

### 2. JobQueue Warning
**Problem**: The application shows warnings about missing JobQueue setup:
```
No `JobQueue` set up. To use `JobQueue`, you must install PTB via `pip install "python-telegram-bot[job-queue]"`
Ignoring `conversation_timeout` because the Application has no JobQueue
```

**Fix**:
- Install the required package: `pip install "python-telegram-bot[job-queue]"`
- This will enable the conversation timeout feature (set to 300 seconds) to work properly

## Deployment Notes

When deploying these fixes:
1. Make the code changes first
2. Install the job-queue extension package if needed
3. Restart the bot
4. Test each button functionality in sequence

For monitoring issues:
- Check application logs for any new errors
- Use the built-in `/logs` command for checking telegram message history
- Pay attention to Google API related errors which might affect functionality 