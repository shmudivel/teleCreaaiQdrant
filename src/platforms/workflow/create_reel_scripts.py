import os
import re
import argparse
import concurrent.futures
import json
from pathlib import Path
import anthropic
import time
import logging
from typing import List, Dict, Tuple, Optional
from .prompts import REEL_GENERATION_PROMPT, REEL_GENERATION_SYSTEM_PROMPT
from .api_utils import create_claude_client, call_claude_api, RateLimiter, exponential_backoff_retry

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Hardcoded API key - Updated to a working key
API_KEY = "REMOVED_API_KEY"

class ReelGenerator:
    """Class to generate Instagram reel scripts from divided text."""
    
    DIVIDER = "--------"
    
    def __init__(self, api_key: str, output_dir: str, overlap_paragraphs: int = 2):
        """Initialize the ReelGenerator.
        
        Args:
            api_key: Anthropic API key
            output_dir: Directory to save output files
            overlap_paragraphs: Number of paragraphs to include from adjacent sections
        """
        self.client = create_claude_client(api_key)
        self.output_dir = output_dir
        self.overlap_paragraphs = overlap_paragraphs
        self.rate_limiter = RateLimiter(calls_per_minute=10)  # Limit to 10 calls per minute
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create subdirectories
        self.reels_dir = os.path.join(output_dir, "reels")
        self.metadata_dir = os.path.join(output_dir, "metadata")
        os.makedirs(self.reels_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
    
    def read_analyzed_text(self, filepath: str) -> str:
        """Read the analyzed text file.
        
        Args:
            filepath: Path to the analyzed text file
            
        Returns:
            The content of the file
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def split_into_sections(self, text: str) -> List[str]:
        """Split the text into sections based on divider lines.
        
        Args:
            text: The analyzed text with dividers
            
        Returns:
            List of text sections
        """
        # Split by divider
        sections = re.split(r'\n\s*' + re.escape(self.DIVIDER) + r'\s*\n', text)
        return [section.strip() for section in sections if section.strip()]
    
    def extract_section_titles(self, sections: List[str]) -> List[Tuple[str, str]]:
        """Extract titles from sections and return (title, content) pairs.
        
        Args:
            sections: List of text sections
            
        Returns:
            List of (title, content) tuples
        """
        titled_sections = []
        
        for section in sections:
            lines = section.split('\n', 1)
            if len(lines) > 1:
                # First line is likely a title if it's relatively short
                first_line = lines[0].strip()
                if len(first_line) < 100:  # Assume it's a title if <100 chars
                    title = first_line
                    content = lines[1].strip()
                else:
                    title = first_line[:50] + "..."  # Create title from beginning
                    content = section
            else:
                # If only one line or very short, use first few words as title
                words = section.split()[:5]
                title = " ".join(words) + "..."
                content = section
                
            titled_sections.append((title, content))
            
        return titled_sections
    
    def add_context_to_sections(self, titled_sections: List[Tuple[str, str]]) -> List[Dict]:
        """Process sections without adding context from adjacent sections.
        
        Args:
            titled_sections: List of (title, content) tuples
            
        Returns:
            List of section dicts
        """
        enriched_sections = []
        total_sections = len(titled_sections)
        
        for i, (title, content) in enumerate(titled_sections):
            section_dict = {
                "id": i + 1,
                "title": title,
                "content": content,
                "total_sections": total_sections
            }
            
            enriched_sections.append(section_dict)
            
        return enriched_sections
    
    @exponential_backoff_retry()
    def generate_reel_script(self, section: Dict) -> Dict:
        """Generate an Instagram reel script for a section using Claude.
        
        Args:
            section: Section dict with content
            
        Returns:
            Dictionary with the reel script and metadata
        """
        # Format the prompt with section data
        formatted_prompt = REEL_GENERATION_PROMPT.format(
            title=section["title"], 
            content=section["content"]
        )
        
        try:
            # Use rate limiter to enforce API limits
            with self.rate_limiter:
                logger.info(f"Generating script for section {section['id']}")
                
                result = call_claude_api(
                    client=self.client,
                    model="claude-3-7-sonnet-20250219",
                    prompt=formatted_prompt,
                    system=REEL_GENERATION_SYSTEM_PROMPT,
                    max_tokens=1500,
                    temperature=0.7
                )
            
            # Extract JSON from response
            try:
                # Find JSON in the response - it should be the entire response but just in case
                json_match = re.search(r'(\{.*\})', result, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    reel_data = json.loads(json_str)
                    
                    return reel_data
                else:
                    logger.error(f"No JSON found in response for section {section['id']}")
                    return self._create_fallback_reel_data(section)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from response for section {section['id']}")
                logger.error(f"Raw response: {result}")
                return self._create_fallback_reel_data(section)
                
        except Exception as e:
            logger.error(f"Error generating reel script for section {section['id']}: {str(e)}")
            return self._create_fallback_reel_data(section)
    
    def _create_fallback_reel_data(self, section: Dict) -> Dict:
        """Create fallback reel data if API call fails.
        
        Args:
            section: Section dict
            
        Returns:
            Basic reel data
        """
        # Create a better title if original is too long
        title = section["title"]
        if len(title) > 60:
            words = title.split()
            title = " ".join(words[:5]) + "..."
        
        # Create a better description
        topic = title.replace("Урок", "уроке").replace(".", "")
        description = f"Важная информация о {topic}. Полезные советы для профессионального роста и развития карьеры."
        
        return {
            "heygen_script": section["content"],
            "title": title,
            "description": description,
            "hashtags": ["#контент", "#обучение", "#развитие", "#бизнес", "#карьера"]
        }
    
    def process_sections_parallel(self, sections: List[Dict], max_workers: int = 4) -> List[Dict]:
        """Process sections in parallel.
        
        Args:
            sections: List of section dictionaries
            max_workers: Maximum number of concurrent workers
            
        Returns:
            List of processed section dictionaries with reel scripts
        """
        processed_sections = []
        
        # Limiting max_workers prevents hitting rate limits too fast
        # Using a smaller number is safer
        adjusted_workers = min(max_workers, 4)
        logger.info(f"Processing sections with {adjusted_workers} workers")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=adjusted_workers) as executor:
            future_to_section = {executor.submit(self.generate_reel_script, section): section for section in sections}
            
            for future in concurrent.futures.as_completed(future_to_section):
                section = future_to_section[future]
                try:
                    reel_data = future.result()
                    # Add minimal section info for file naming
                    reel_data["_section_id"] = section["id"]
                    reel_data["_section_title"] = section["title"]
                    reel_data["_total_sections"] = section["total_sections"]
                    processed_sections.append(reel_data)
                    logger.info(f"Processed section {section['id']} of {section['total_sections']}")
                except Exception as e:
                    logger.error(f"Error processing section {section['id']}: {str(e)}")
                    fallback = self._create_fallback_reel_data(section)
                    fallback["_section_id"] = section["id"]
                    fallback["_section_title"] = section["title"]
                    fallback["_total_sections"] = section["total_sections"]
                    processed_sections.append(fallback)
        
        # Sort by section ID to maintain order
        processed_sections.sort(key=lambda x: x["_section_id"])
        return processed_sections
    
    def save_reel_scripts(self, processed_sections: List[Dict]) -> None:
        """Save reel scripts to files.
        
        Args:
            processed_sections: List of processed section dicts with reel scripts
        """
        for section in processed_sections:
            section_id = section["_section_id"]
            total_sections = section["_total_sections"]
            section_title = section["_section_title"]
            
            # Save HeyGen script (just the spoken text)
            heygen_filename = f"heygen_{section_id:02d}_of_{total_sections:02d}_{self._sanitize_filename(section_title)}.txt"
            heygen_path = os.path.join(self.reels_dir, heygen_filename)
            
            with open(heygen_path, 'w', encoding='utf-8') as f:
                # Add title as a comment at the top of the file for easy reference
                f.write(f"# {section.get('title', section_title)}\n\n")
                f.write(section["heygen_script"])
            
            # Save metadata as JSON (without the internal fields)
            clean_section = {k: v for k, v in section.items() if not k.startswith('_')}
            metadata_filename = f"metadata_{section_id:02d}.json"
            metadata_path = os.path.join(self.metadata_dir, metadata_filename)
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(clean_section, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved reel script for section {section_id} to {heygen_path}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a string to be used as a filename.
        
        Args:
            filename: String to sanitize
            
        Returns:
            Sanitized string
        """
        # Replace non-alphanumeric characters with underscore
        sanitized = re.sub(r'[^\w\s-]', '_', filename)
        # Replace multiple spaces with underscore
        sanitized = re.sub(r'\s+', '_', sanitized)
        # Limit length
        return sanitized[:50]
    
    def process_file(self, input_filepath: str, max_workers: int = 4) -> None:
        """Process the analyzed text file and generate reel scripts.
        
        Args:
            input_filepath: Path to the analyzed text file
            max_workers: Maximum number of parallel workers
        """
        logger.info(f"Processing file: {input_filepath}")
        
        # Read and parse the text
        text = self.read_analyzed_text(input_filepath)
        
        # Split into sections
        sections = self.split_into_sections(text)
        logger.info(f"Split text into {len(sections)} sections")
        
        # Extract titles
        titled_sections = self.extract_section_titles(sections)
        
        # Add context
        enriched_sections = self.add_context_to_sections(titled_sections)
        
        # Process sections in parallel
        processed_sections = self.process_sections_parallel(enriched_sections, max_workers)
        
        # Save results
        self.save_reel_scripts(processed_sections)
        
        logger.info(f"Completed processing. Generated {len(processed_sections)} reel scripts.")
        logger.info(f"Output saved to: {self.reels_dir}")

def main():
    """Main function to parse arguments and run the reel generation."""
    parser = argparse.ArgumentParser(description='Generate Instagram reel scripts from divided text')
    parser.add_argument('--input', required=True, help='Path to the analyzed text file')
    parser.add_argument('--output', default='output', help='Directory to save output files')
    parser.add_argument('--overlap', type=int, default=2, help='Number of paragraphs to include from adjacent sections')
    parser.add_argument('--workers', type=int, default=4, help='Maximum number of parallel workers')
    parser.add_argument('--sections', help='Specific section numbers to process (comma-separated, e.g., "1,3,5")')
    parser.add_argument('--count', type=int, help='Number of reels to generate, starting from the beginning')
    
    args = parser.parse_args()
    
    # Use the hardcoded API key
    api_key = API_KEY
    
    # Create and run generator
    generator = ReelGenerator(
        api_key=api_key,
        output_dir=args.output,
        overlap_paragraphs=args.overlap
    )
    
    # Process specific sections if requested
    if args.sections:
        try:
            section_numbers = [int(s.strip()) for s in args.sections.split(',')]
            # Read and parse the text
            text = generator.read_analyzed_text(args.input)
            
            # Split into sections
            sections = generator.split_into_sections(text)
            logger.info(f"Split text into {len(sections)} sections")
            
            # Extract titles
            titled_sections = generator.extract_section_titles(sections)
            
            # Add context
            all_enriched_sections = generator.add_context_to_sections(titled_sections)
            
            # Filter sections by selected numbers
            # Adjust section numbers to be 1-indexed for user-friendliness
            enriched_sections = [s for s in all_enriched_sections if s['id'] in section_numbers]
            
            if not enriched_sections:
                logger.error(f"No valid sections found with numbers: {section_numbers}")
                logger.info(f"Available section numbers are 1-{len(sections)}")
                return
                
            logger.info(f"Processing {len(enriched_sections)} selected sections: {section_numbers}")
            
            # Process selected sections in parallel
            processed_sections = generator.process_sections_parallel(enriched_sections, args.workers)
            
            # Save results
            generator.save_reel_scripts(processed_sections)
            
            logger.info(f"Completed processing. Generated {len(processed_sections)} reel scripts.")
            logger.info(f"Output saved to: {generator.reels_dir}")
        except ValueError as e:
            logger.error(f"Error parsing section numbers: {e}")
            return
    elif args.count:
        try:
            # Read and parse the text
            text = generator.read_analyzed_text(args.input)
            
            # Split into sections
            sections = generator.split_into_sections(text)
            logger.info(f"Split text into {len(sections)} sections")
            
            # Extract titles
            titled_sections = generator.extract_section_titles(sections)
            
            # Add context
            all_enriched_sections = generator.add_context_to_sections(titled_sections)
            
            # Take first N sections
            count = min(args.count, len(all_enriched_sections))
            enriched_sections = all_enriched_sections[:count]
            
            logger.info(f"Processing first {count} sections")
            
            # Process selected sections in parallel
            processed_sections = generator.process_sections_parallel(enriched_sections, args.workers)
            
            # Save results
            generator.save_reel_scripts(processed_sections)
            
            logger.info(f"Completed processing. Generated {len(processed_sections)} reel scripts.")
            logger.info(f"Output saved to: {generator.reels_dir}")
        except Exception as e:
            logger.error(f"Error processing sections: {e}")
            return
    else:
        # Process all sections
        generator.process_file(
            input_filepath=args.input,
            max_workers=args.workers
        )

if __name__ == "__main__":
    main() 