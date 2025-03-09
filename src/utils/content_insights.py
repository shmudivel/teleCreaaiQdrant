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
        
        # Store the original analyzed parts for full analysis access
        self.original_parts = analyzed_parts
        self.full_analysis_data = None
        
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
                
        # Try to parse the first part for full analysis access (if it's in the new format)
        if analyzed_parts and len(analyzed_parts) > 0:
            try:
                first_part = analyzed_parts[0]
                data = json.loads(first_part) if isinstance(first_part, str) else first_part
                
                # Check if this is in the new format with holistic_analysis
                if "holistic_analysis" in data or "dzen_potential" in data:
                    self.full_analysis_data = data
            except Exception:
                pass
    
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
    
    def get_full_analysis(self):
        """
        Get the full analysis data for all parts.
        This is used by the new enhanced agents to access detailed style and tone information.
        
        Returns:
            dict or None: The full analysis data if available, or None if not available
        """
        # If we have the new format data already parsed, return it
        if self.full_analysis_data:
            return self.full_analysis_data
            
        # If not, try to combine the original parts into a unified structure
        # This is for backward compatibility
        if not self.original_parts or len(self.original_parts) == 0:
            return None
            
        try:
            # Try to use the first part as a template for the full structure
            first_part = self.original_parts[0]
            combined_data = json.loads(first_part) if isinstance(first_part, str) else first_part
            
            # Create a minimal structure if we can't parse the first part properly
            if not isinstance(combined_data, dict):
                combined_data = {
                    "parts": [],
                    "holistic_analysis": {
                        "overall_style": "Не определен",
                        "coherence": "Не определена",
                        "emotional_triggers": [],
                        "author_uniqueness": []
                    },
                    "dzen_potential": {
                        "attention_hooks": self.engagement_data.get("headline_triggers", []),
                        "emotional_points": self.engagement_data.get("emotional_points", []),
                        "discussion_topics": self.engagement_data.get("discussion_topics", []),
                        "audience_relevance": "Не определена"
                    }
                }
            
            # Make sure we have the parts key
            if "parts" not in combined_data:
                combined_data["parts"] = []
                
            # Add each processed part
            for i, part in enumerate(self.parts):
                if i < len(combined_data["parts"]):
                    continue  # Skip if already in the structure
                    
                # Create a compatible part structure
                new_part = {
                    "marker": part.get("marker", f"--- Part {i+1} ---"),
                    "tone_analysis": {
                        "emotional_tone": part.get("tone", "Не определен"),
                        "lexical_features": "Не определены",
                        "syntax_patterns": "Не определены",
                        "rhetorical_devices": "Не определены",
                        "author_voice": "Не определен"
                    },
                    "key_elements": {
                        "facts": part.get("facts", []),
                        "personal_stories": part.get("personal_stories", []),
                        "main_ideas": [],
                        "unique_insights": []
                    },
                    "content_analysis": {
                        "main_idea": "Не определена",
                        "paragraph_connections": "Не определены",
                        "key_essence": part.get("key_essence", "Не определена"),
                        "logic_path": "Не определен",
                        "author_intention": "Не определена"
                    }
                }
                
                combined_data["parts"].append(new_part)
                
            return combined_data
                
        except Exception as e:
            logger.warning(f"Error creating full analysis: {str(e)}")
            return None
    
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
        
    def get_final_enhancement(self):
        """
        Get enhancement data for final editing.
        Used by the new enhanced DzenAgents for final editing.
        This method is for compatibility with the updated agents.
        
        Returns:
            dict: Enhancement data with holistic analysis for final editing
        """
        # Try to get holistic analysis from full analysis
        full_data = self.get_full_analysis()
        
        if full_data and isinstance(full_data, dict):
            try:
                # Extract holistic analysis and dzen potential
                holistic = full_data.get("holistic_analysis", {})
                dzen_data = full_data.get("dzen_potential", {})
                
                # Combine into a unified format
                return {
                    "overall_style": holistic.get("overall_style", "Не определен"),
                    "coherence": holistic.get("coherence", "Не определена"),
                    "emotional_triggers": holistic.get("emotional_triggers", []),
                    "author_uniqueness": holistic.get("author_uniqueness", []),
                    "attention_hooks": dzen_data.get("attention_hooks", []),
                    "emotional_points": dzen_data.get("emotional_points", []),
                    "discussion_topics": dzen_data.get("discussion_topics", []),
                    "audience_relevance": dzen_data.get("audience_relevance", "Не определена")
                }
            except Exception as e:
                logger.warning(f"Error extracting final enhancement: {str(e)}")
        
        # Fall back to the older format if needed
        return self.get_final_editing_data() 