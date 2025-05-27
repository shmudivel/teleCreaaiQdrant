class WorkflowTasks:
    """Tasks for content workflow from Google Docs to YouTube."""
    
    def google_doc_to_reels_task(self, doc_url, output_dir=None, top_n=10):
        """
        Process a Google Doc and convert it to reels
        
        Args:
            doc_url: URL of the Google Doc to process
            output_dir: Directory to save output files (optional)
            top_n: Number of top reels to select (default: 10)
            
        Returns:
            Dictionary with paths to generated content
        """
        from .integration import process_google_doc_to_reels
        
        return process_google_doc_to_reels(doc_url, output_dir, top_n)
        
    def process_selected_reel_task(self, metadata):
        """
        Process a selected reel - generate HeyGen video and upload to YouTube
        
        Args:
            metadata: The metadata dictionary for the selected reel
            
        Returns:
            Boolean indicating success or failure
        """
        from .integration import process_selected_reel
        
        return process_selected_reel(metadata)
        
    def google_doc_to_single_video_task(self, doc_url, output_dir=None):
        """
        Process a Google Doc and convert it to a single video
        
        Args:
            doc_url: URL of the Google Doc to process
            output_dir: Directory to save output files (optional)
            
        Returns:
            Dictionary with paths to generated content
        """
        from .single_video.integration_for_single_video import process_google_doc_to_single_video
        
        return process_google_doc_to_single_video(doc_url, output_dir) 