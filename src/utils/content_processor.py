import logging
from crewai import Crew
from src.platforms.factory import PlatformFactory
from src.utils.google_services import save_to_google_drive
from src.text_splitter import split_text_into_parts
import json

# Configure logging
logger = logging.getLogger(__name__)

async def process_content_parts(platform, content_parts_data, message):
    """
    Process content parts with CrewAI and platform-specific agents.
    
    Args:
        platform (str): Platform identifier (e.g., 'dzen', 'vc')
        content_parts_data (tuple): Tuple containing (analyzed_parts, insights_processor)
        message (telegram.Message): Message object for updating the user
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    try:
        # Unpack the content parts data
        if isinstance(content_parts_data, tuple) and len(content_parts_data) == 2:
            content_parts, insights_processor = content_parts_data
        else:
            # For backward compatibility
            content_parts = content_parts_data
            insights_processor = None
            
        # Get platform-specific agents and tasks
        agents_class = PlatformFactory.get_platform_agents(platform, insights_processor)
        tasks_class = PlatformFactory.get_platform_tasks(platform)
        
        # Validate that we have enough parts
        if len(content_parts) < 4:
            logger.warning(f"Not enough parts generated. Expected at least 4, got {len(content_parts)}")
            # Pad the parts list with empty strings if needed
            while len(content_parts) < 4:
                content_parts.append("")
        
        # Create agents with insights
        content_agent1 = agents_class.content_creator_agent()
        content_agent2 = agents_class.content_creator_agent_part2()
        content_agent3 = agents_class.content_creator_agent_part3()
        content_agent4 = agents_class.content_creator_agent_part4()
        
        # Create tasks for each part
        creation_task1 = tasks_class.content_creation_task(content_agent1, content_parts[0])
        creation_task2 = tasks_class.content_creation_task_part2(content_agent2, content_parts[1])
        creation_task3 = tasks_class.content_creation_task_part3(content_agent3, content_parts[2])
        creation_task4 = tasks_class.content_creation_task_part4(content_agent4, content_parts[3])
        
        # Set up the crew with all agents and tasks
        crew = Crew(
            agents=[content_agent1, content_agent2, content_agent3, content_agent4],
            tasks=[creation_task1, creation_task2, creation_task3, creation_task4]
        )
        
        await message.reply_text("Начинаю обработку контента (это может занять некоторое время)...")
        
        # Run all tasks
        result = crew.kickoff()
        
        # Combine all results
        combined_output = f"""
--- Part 1 ---
{creation_task1.output}

--- Part 2 ---
{creation_task2.output}

--- Part 3 ---
{creation_task3.output}

--- Part 4 ---
{creation_task4.output}
"""
        
        # Create final editor agent
        final_editor = agents_class.final_editor_agent()
        
        # Create task for final editing
        final_editing_task = tasks_class.final_editing_task(final_editor, combined_output)
        
        # Final crew with final editor only
        final_crew = Crew(
            agents=[final_editor],
            tasks=[final_editing_task]
        )

        await message.reply_text("Выполняю финальную редакцию поста...")

        # Run final editing
        final_result = final_crew.kickoff()

        # Get platform display name for the document
        platforms = PlatformFactory.get_available_platforms()
        platform_name = platforms.get(platform, platform)

        # Use the final edited result for saving
        post_link = save_to_google_drive(
            final_editing_task.output, 
            "Source content", 
            platform_name
        )
        
        # Send the result
        await message.reply_text(f"✅ Пост для {platform_name} готов!")
        
        if post_link:
            await message.reply_text(f"Ссылка на пост: {post_link}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in process_content_parts: {str(e)}")
        raise e 