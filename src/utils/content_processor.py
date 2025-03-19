import logging
from crewai import Crew
from src.platforms.factory import PlatformFactory
from src.utils.google_services import save_to_google_drive
from src.text_splitter import split_text_into_parts
from src.utils.content_reviewer import ContentReviewer
import json
import traceback
import inspect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_task_output_as_string(task, default=""):
    """
    Safely extract string output from a CrewAI task.
    
    Args:
        task: The CrewAI task object
        default: Default value to return if output cannot be extracted
        
    Returns:
        str: The task output as a string
    """
    try:
        if task is None:
            return default
            
        if task.output is None:
            return default
            
        # Log the output type to help with debugging
        logger.info(f"Task output type: {type(task.output)}")
        
        # Handle different output types
        if isinstance(task.output, str):
            return task.output
        else:
            # Attempt to convert to string
            return str(task.output)
    except Exception as e:
        logger.error(f"Error extracting task output: {str(e)}")
        return default

def log_object_details(obj, prefix=""):
    """
    Log details about an object for debugging purposes.
    
    Args:
        obj: The object to inspect
        prefix: Prefix for log messages
    """
    try:
        logger.info(f"{prefix} Object type: {type(obj)}")
        if hasattr(obj, '__dict__'):
            attrs = {k: v for k, v in vars(obj).items() if not k.startswith('_')}
            logger.info(f"{prefix} Attributes: {list(attrs.keys())}")
            
        if hasattr(obj, 'tools'):
            if callable(obj.tools):
                logger.info(f"{prefix} Has tools() method")
                try:
                    tools = obj.tools()
                    logger.info(f"{prefix} Tools (from method): {[t.name if hasattr(t, 'name') else type(t).__name__ for t in tools]}")
                except Exception as e:
                    logger.error(f"{prefix} Error calling tools() method: {str(e)}")
            else:
                logger.info(f"{prefix} Tools attribute: {[t.name if hasattr(t, 'name') else type(t).__name__ for t in obj.tools]}")
    except Exception as e:
        logger.error(f"Error logging object details: {str(e)}")
        logger.error(traceback.format_exc())

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
        logger.info(f"Getting platform agents for: {platform}")
        try:
            agents_class = PlatformFactory.get_platform_agents(platform, insights_processor)
            logger.info(f"Successfully created agents class for {platform}")
        except Exception as e:
            logger.error(f"Error getting platform agents: {str(e)}")
            logger.error(traceback.format_exc())
            await message.reply_text(f"❌ Ошибка при создании агентов для платформы {platform}: {str(e)}")
            return False
            
        try:
            tasks_class = PlatformFactory.get_platform_tasks(platform)
            logger.info(f"Successfully created tasks class for {platform}")
        except Exception as e:
            logger.error(f"Error getting platform tasks: {str(e)}")
            logger.error(traceback.format_exc())
            await message.reply_text(f"❌ Ошибка при создании задач для платформы {platform}: {str(e)}")
            return False
        
        # Log details about the agents class
        log_object_details(agents_class, f"[{platform} AgentsClass]")
        
        # Validate that we have enough parts
        if len(content_parts) < 4:
            logger.warning(f"Not enough parts generated. Expected at least 4, got {len(content_parts)}")
            # Pad the parts list with empty strings if needed
            while len(content_parts) < 4:
                content_parts.append("")
        
        # Create agents with insights - wrap each in try/except for better error isolation
        try:
            logger.info("Creating content agent 1")
            content_agent1 = agents_class.content_creator_agent()
            log_object_details(content_agent1, "[Agent1]")
        except Exception as e:
            error_msg = f"Error creating agent 1: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            await message.reply_text(f"❌ {error_msg}")
            return False
        
        try:
            logger.info("Creating content agent 2")
            content_agent2 = agents_class.content_creator_agent_part2()
            log_object_details(content_agent2, "[Agent2]")
        except Exception as e:
            error_msg = f"Error creating agent 2: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            await message.reply_text(f"❌ {error_msg}")
            return False
        
        try:
            logger.info("Creating content agent 3")
            content_agent3 = agents_class.content_creator_agent_part3()
            log_object_details(content_agent3, "[Agent3]")
        except Exception as e:
            error_msg = f"Error creating agent 3: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            await message.reply_text(f"❌ {error_msg}")
            return False
        
        try:
            logger.info("Creating content agent 4")
            content_agent4 = agents_class.content_creator_agent_part4()
            log_object_details(content_agent4, "[Agent4]")
        except Exception as e:
            error_msg = f"Error creating agent 4: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            await message.reply_text(f"❌ {error_msg}")
            return False
        
        # Create tasks for each part
        try:
            logger.info("Creating content creation tasks")
            creation_task1 = tasks_class.content_creation_task(content_agent1, content_parts[0])
            creation_task2 = tasks_class.content_creation_task_part2(content_agent2, content_parts[1])
            creation_task3 = tasks_class.content_creation_task_part3(content_agent3, content_parts[2])
            creation_task4 = tasks_class.content_creation_task_part4(content_agent4, content_parts[3])
            logger.info("Successfully created all tasks")
        except Exception as e:
            error_msg = f"Error creating tasks: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            await message.reply_text(f"❌ {error_msg}")
            return False
        
        # Set up the crew with all agents and tasks
        try:
            logger.info("Creating crew with all agents and tasks")
            crew = Crew(
                agents=[content_agent1, content_agent2, content_agent3, content_agent4],
                tasks=[creation_task1, creation_task2, creation_task3, creation_task4]
            )
            logger.info("Successfully created crew")
        except Exception as e:
            error_msg = f"Error creating crew: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            await message.reply_text(f"❌ {error_msg}")
            return False
        
        await message.reply_text("Начинаю обработку контента (это может занять некоторое время)...")
        
        # Run all tasks
        try:
            logger.info("Starting crew kickoff for content creation")
            result = crew.kickoff()
            logger.info("Content creation crew completed")
        except Exception as e:
            error_msg = f"Error during crew execution: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            await message.reply_text(f"❌ {error_msg}")
            return False
        
        # Log task output types for debugging
        logger.info(f"Task 1 output type: {type(creation_task1.output) if hasattr(creation_task1, 'output') else 'None'}")
        logger.info(f"Task 2 output type: {type(creation_task2.output) if hasattr(creation_task2, 'output') else 'None'}")
        logger.info(f"Task 3 output type: {type(creation_task3.output) if hasattr(creation_task3, 'output') else 'None'}")
        logger.info(f"Task 4 output type: {type(creation_task4.output) if hasattr(creation_task4, 'output') else 'None'}")
        
        # Extract task outputs as strings using the helper function
        task1_output = get_task_output_as_string(creation_task1)
        task2_output = get_task_output_as_string(creation_task2)
        task3_output = get_task_output_as_string(creation_task3)
        task4_output = get_task_output_as_string(creation_task4)
        
        # Combine all results
        combined_output = f"""
--- Part 1 ---
{task1_output}

--- Part 2 ---
{task2_output}

--- Part 3 ---
{task3_output}

--- Part 4 ---
{task4_output}
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
        
        # Log final editing task output type
        logger.info(f"Final editing task output type: {type(final_editing_task.output) if hasattr(final_editing_task, 'output') else 'None'}")
        
        # Get final editing result as string
        final_editing_result = get_task_output_as_string(final_editing_task)

        # Check for quality issues using ContentReviewer
        await message.reply_text("Проверяю качество контента...")
        
        content_reviewer = ContentReviewer(author_name="Сергей Черненко")
        review_summary = content_reviewer.get_review_summary(final_editing_result)
        
        # If there are significant issues, try to fix them automatically
        if "❌" in review_summary:
            await message.reply_text("Обнаружены проблемы с контентом, выполняю автоматическое исправление...")
            
            # Fix common issues
            fixed_content = content_reviewer.fix_common_issues(final_editing_result)
            
            # Check if there are still issues after fixing
            post_fix_review = content_reviewer.get_review_summary(fixed_content)
            
            if "❌" in post_fix_review:
                # If there are still issues, log them but proceed with the fixed content
                logger.warning(f"Content still has issues after automatic fixing: \n{post_fix_review}")
                await message.reply_text("Некоторые проблемы остались, но контент улучшен. Продолжаю...")
                
                # Send detailed report in production environment
                if "prod" in platform:
                    detailed_report = content_reviewer.get_detailed_report(fixed_content)
                    await message.reply_text(f"Детальный отчет о проблемах:\n\n{detailed_report}")
                
                # Use the fixed content
                final_content = fixed_content
            else:
                # All issues fixed
                await message.reply_text("Все проблемы успешно исправлены!")
                final_content = fixed_content
        else:
            # No issues found
            await message.reply_text("Контент прошел проверку качества!")
            final_content = final_editing_result

        # Get platform display name for the document
        platforms = PlatformFactory.get_available_platforms()
        platform_name = platforms.get(platform, platform)

        # Use the final reviewed and potentially fixed content for saving
        post_link = save_to_google_drive(
            final_content, 
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
        logger.error(traceback.format_exc())
        await message.reply_text(f"❌ Произошла ошибка при обработке контента: {str(e)}")
        return False 