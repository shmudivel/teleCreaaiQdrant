from typing import Dict, Type, Any
from .dzen import agents as dzen_agents
from .dzen import tasks as dzen_tasks
from .vc import agents as vc_agents
from .vc import tasks as vc_tasks

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
        }
    }
    
    @classmethod
    def get_platform_agents(cls, platform_name: str):
        """Get the agents for the specified platform."""
        if platform_name not in cls.PLATFORMS:
            raise ValueError(f"Unsupported platform: {platform_name}")
        
        return cls.PLATFORMS[platform_name]["agents"]()
    
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