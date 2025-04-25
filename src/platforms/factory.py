from typing import Dict, Type, Any
from .dzen import agents as dzen_agents
from .dzen import tasks as dzen_tasks
from .vc import agents as vc_agents
from .vc import tasks as vc_tasks
from .vector_db import agents as vector_db_agents
from .vector_db import tasks as vector_db_tasks
from .workflow import agents as workflow_agents
from .workflow import tasks as workflow_tasks

class PlatformFactory:
    """Factory for creating platform-specific agents and tasks."""
    
    PLATFORMS = {
        "dzen": {
            "agents": dzen_agents.DzenAgents,
            "tasks": dzen_tasks.DzenTasks,
            "display_name": "dzen.ru"
        },
        "vc": {
            "agents": vc_agents.VCAgents,
            "tasks": vc_tasks.VCTasks,
            "display_name": "vc.ru"
        },
        "vector_db": {
            "agents": vector_db_agents.VectorDBAgents,
            "tasks": vector_db_tasks.VectorDBTasks,
            "display_name": "Векторная база данных"
        },
        "workflow": {
            "agents": workflow_agents.WorkflowAgents,
            "tasks": workflow_tasks.WorkflowTasks,
            "display_name": "Google Doc to YouTube Workflow"
        }
    }
    
    @classmethod
    def get_platform_agents(cls, platform_name: str, insights_processor=None):
        """
        Get the agents for the specified platform.
        
        Args:
            platform_name (str): The name of the platform
            insights_processor: Optional ContentInsightsProcessor instance
        
        Returns:
            The platform-specific agents class instance
        """
        if platform_name not in cls.PLATFORMS:
            raise ValueError(f"Unsupported platform: {platform_name}")
        
        agent_class = cls.PLATFORMS[platform_name]["agents"]
        
        # If the platform accepts insights_processor and one is provided, pass it
        if insights_processor is not None:
            return agent_class(insights_processor=insights_processor)
        
        return agent_class()
    
    @classmethod
    def get_platform_tasks(cls, platform_name: str):
        """Get the tasks for the specified platform."""
        if platform_name not in cls.PLATFORMS:
            raise ValueError(f"Unsupported platform: {platform_name}")
        
        return cls.PLATFORMS[platform_name]["tasks"]()
    
    @classmethod
    def get_available_platforms(cls) -> Dict[str, str]:
        """Get a dictionary of available platforms (key: platform_id, value: display_name)."""
        return {key: value["display_name"] for key, value in cls.PLATFORMS.items()} 