class WorkflowAgents:
    """Agents for workflow processing from Google Docs to YouTube."""
    
    def __init__(self, insights_processor=None):
        """Initialize the workflow agents.
 
        Args:
            insights_processor: Optional ContentInsightsProcessor instance
        """
        self.insights_processor = insights_processor 