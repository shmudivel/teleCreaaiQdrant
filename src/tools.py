from langchain.agents import tool

class SearchToolset():
    """Base search toolset that can be extended for different search providers"""
    @staticmethod
    def tools():
        return []  # Return empty list as we're using Qdrant directly