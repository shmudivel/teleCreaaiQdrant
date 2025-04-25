import os
import sys
from pathlib import Path

def add_big_text_to_reels_path():
    """Add the tests/big_text_to_reels directory to the Python path."""
    # Get the project root directory (assuming we're in src/platforms/workflow)
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent.parent
    
    # Path to the big_text_to_reels directory
    big_text_to_reels_path = str(project_root / 'tests' / 'big_text_to_reels')
    
    # Add to Python path if not already there
    if big_text_to_reels_path not in sys.path:
        sys.path.append(big_text_to_reels_path)
        print(f"Added {big_text_to_reels_path} to Python path") 