import json
import logging
from json.decoder import JSONDecodeError
from src.text_analyzer import extract_insights

# Configure logging
logger = logging.getLogger(__name__)

class ContentInsightsProcessor:
    """
    Process structured insights from text analysis to enhance content creation.
    This utility helps agents leverage the structured JSON data for better content creation.
    """
    
    def __init__(self, analyzed_parts):
        """
        Initialize the processor with analyzed text parts.
        
        Args:
            analyzed_parts (list): List of JSON strings from analyze_text_structure
        """
        self.parts = []
        self.engagement_data = {
            "headline_triggers": [],
            "emotional_points": [],
            "discussion_topics": []
        }
        self.expertise = []
        
        # Process each part
        for i, part_json in enumerate(analyzed_parts):
            try:
                # Try to parse as JSON
                self._process_part(part_json, i+1)
            except (JSONDecodeError, TypeError, KeyError) as e:
                logger.warning(f"Part {i+1} could not be parsed as JSON: {str(e)}")
                # Store as raw text if it's not valid JSON
                self.parts.append({
                    "marker": f"--- Part {i+1} ---",
                    "raw_text": part_json,
                    "is_structured": False
                })
    
    def _process_part(self, part_json, part_num):
        """Process a single part JSON."""
        # Try to extract part data from the JSON
        data = json.loads(part_json) if isinstance(part_json, str) else part_json
        
        # Find the matching part in the JSON data
        part_data = None
        marker = f"--- Part {part_num} ---"
        
        for part in data.get("parts", []):
            if part.get("marker") == marker:
                part_data = part
                break
        
        if not part_data:
            # If not found in the structure, create a basic one
            part_data = {
                "marker": marker,
                "raw_text": part_json,
                "is_structured": True
            }
        else:
            part_data["is_structured"] = True
        
        self.parts.append(part_data)
        
        # Collect engagement data
        for key in self.engagement_data.keys():
            values = data.get("engagement", {}).get(key, [])
            if values:
                self.engagement_data[key].extend(values)
        
        # Collect expertise data
        expertise = data.get("expertise", [])
        if expertise:
            self.expertise.extend(expertise)
    
    def get_part_enhancement(self, part_num):
        """
        Get enhancement data for a specific part to be used by content creation agents.
        
        Args:
            part_num (int): Part number (1-based)
            
        Returns:
            dict: Enhancement data for the specified part
        """
        if part_num < 1 or part_num > len(self.parts):
            return {"error": f"Part {part_num} does not exist"}
        
        part = self.parts[part_num - 1]
        
        if not part.get("is_structured", False):
            return {"error": "Part data is not structured", "raw_text": part.get("raw_text", "")}
        
        # Build enhancement based on part data and global engagement data
        enhancement = {
            "tone": part.get("tone", ""),
            "key_facts": part.get("facts", []),
            "personal_stories": part.get("personal_stories", []),
            "key_essence": part.get("key_essence", ""),
            "headline_options": self._get_relevant_headline_triggers(part_num),
            "emotional_hooks": self._get_relevant_emotional_points(part_num),
            "expertise_highlights": self._get_relevant_expertise(part_num)
        }
        
        return enhancement
    
    def _get_relevant_headline_triggers(self, part_num):
        """Get headline triggers relevant to this part."""
        # For part 1, we want all headline triggers
        if part_num == 1:
            return self.engagement_data.get("headline_triggers", [])
        return []
    
    def _get_relevant_emotional_points(self, part_num):
        """Get emotional points relevant to this part."""
        # Distribute emotional points across parts
        all_points = self.engagement_data.get("emotional_points", [])
        if not all_points:
            return []
            
        # Simple distribution - each part gets some points
        points_per_part = max(1, len(all_points) // len(self.parts))
        start_idx = (part_num - 1) * points_per_part
        end_idx = start_idx + points_per_part
        
        return all_points[start_idx:min(end_idx, len(all_points))]
    
    def _get_relevant_expertise(self, part_num):
        """Get expertise highlights relevant to this part."""
        # Parts 1 and 4 get expertise highlights
        if part_num in [1, 4]:
            return self.expertise
        return []
    
    def get_final_editing_data(self):
        """
        Get consolidated data to help with final editing.
        
        Returns:
            dict: Consolidated data for final editing
        """
        return {
            "part_essences": [part.get("key_essence", "") for part in self.parts],
            "all_headline_triggers": self.engagement_data.get("headline_triggers", []),
            "all_emotional_points": self.engagement_data.get("emotional_points", []),
            "discussion_topics": self.engagement_data.get("discussion_topics", []),
            "expertise": self.expertise
        } 