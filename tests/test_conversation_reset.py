import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bot import (
    start, 
    handle_menu_selection, 
    handle_transcription_input, 
    handle_vector_db_query,
    ConversationHandler,
    show_main_menu
)

class TestConversationReset(unittest.TestCase):
    def setUp(self):
        # Create mock objects for Update and Context
        self.update = MagicMock()
        self.context = MagicMock()
        
        # Setup user_data dict in context
        self.context.user_data = {}
        
        # Setup effective_user
        self.update.effective_user = MagicMock()
        self.update.effective_user.id = 12345
        
        # Setup message and callback_query
        self.update.message = AsyncMock()
        self.update.callback_query = AsyncMock()
        
    async def test_start_clears_user_data(self):
        """Test that the start command properly clears user data"""
        # Set some initial data in context
        self.context.user_data['flow'] = 'previous_flow'
        self.context.user_data['selected_platform'] = 'previous_platform'
        
        # Call start command
        result = await start(self.update, self.context)
        
        # Verify that user_data is cleared
        self.assertEqual(len(self.context.user_data), 0)
        self.assertIsNone(self.context.user_data.get('flow'))
        self.assertEqual(result, ConversationHandler.END)
    
    async def test_handle_transcription_input_ends_conversation(self):
        """Test that handle_transcription_input properly ends the conversation"""
        # Setup necessary data
        self.context.user_data['url'] = 'https://example.com'
        self.update.message.text = 'Test transcription'
        
        # Mock save_telegram_message_to_sheet to return success
        with patch('src.bot.save_telegram_message_to_sheet', return_value={'success': True, 'sheet_url': 'https://sheets.example.com'}):
            result = await handle_transcription_input(self.update, self.context)
            
            # Verify conversation ends
            self.assertEqual(result, ConversationHandler.END)
    
    async def test_handle_vector_db_query_ends_conversation(self):
        """Test that handle_vector_db_query properly ends the conversation"""
        # Setup query text
        self.update.message.text = 'Test question for Sergey'
        
        # Mock VectorDBIntegration
        with patch('src.platforms.vector_db.VectorDBIntegration') as mock_vector_db:
            # Configure the mock to return a response
            instance = mock_vector_db.return_value
            instance.process_query.return_value = "Test response from Sergey"
            
            result = await handle_vector_db_query(self.update, self.context)
            
            # Verify conversation ends
            self.assertEqual(result, ConversationHandler.END)
    
    async def test_multiple_workflow_sequence(self):
        """Test a sequence of workflows to ensure state is properly reset"""
        # First workflow: Google Sheet update
        self.update.callback_query.data = "menu_update_sheet"
        
        # Call menu selection handler
        await handle_menu_selection(self.update, self.context)
        
        # Verify context data is set correctly
        self.assertEqual(self.context.user_data.get('flow'), 'update_sheet')
        
        # Complete the workflow
        self.context.user_data['url'] = 'https://example.com'
        self.update.message.text = 'Test transcription'
        
        # Mock save_telegram_message_to_sheet to return success
        with patch('src.bot.save_telegram_message_to_sheet', return_value={'success': True, 'sheet_url': 'https://sheets.example.com'}):
            result = await handle_transcription_input(self.update, self.context)
            
            # Verify conversation ends
            self.assertEqual(result, ConversationHandler.END)
        
        # Start a new workflow
        # This should simulate a user starting a new workflow after completing the previous one
        self.update.callback_query.data = "menu_vector_db"
        
        # Call menu selection handler
        result = await handle_menu_selection(self.update, self.context)
        
        # Verify context data is updated for the new workflow
        self.assertEqual(self.context.user_data.get('flow'), 'vector_db_query')
        self.assertNotEqual(result, ConversationHandler.END)  # Should still be in conversation

if __name__ == '__main__':
    # Setup asyncio test runner
    loop = asyncio.get_event_loop()
    unittest.main() 