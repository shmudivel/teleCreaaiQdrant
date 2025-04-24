import os
import argparse
import datetime
import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import modules from existing scripts
from analyze_google_doc import extract_doc_id_from_url, get_document_content, analyze_with_claude
from create_reel_scripts import ReelGenerator
from reel_picker import load_metadata_files, analyze_viral_potential, select_top_reels, save_top_reels, get_client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_google_doc(url: str, service_account_file: str) -> str:
    """Process a Google Doc and divide it into sections.
    
    Args:
        url: Google Doc URL
        service_account_file: Path to service account JSON file
    
    Returns:
        Path to the created analyzed text file
    """
    logger.info("Step 1: Analyzing Google Doc")
    logger.info(f"Extracting content from: {url}")
    
    # Extract document ID from URL
    doc_id = extract_doc_id_from_url(url)
    logger.info(f"Document ID: {doc_id}")
    
    # Get document content
    content = get_document_content(doc_id, service_account_file)
    logger.info(f"Retrieved {len(content)} characters from the document")
    
    # Analyze with Claude
    logger.info("Analyzing content with Claude...")
    analyzed_text = analyze_with_claude(content)
    
    # Create output file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(script_dir, f"analyzed_doc_{timestamp}.txt")
    
    # Write the analyzed text to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(analyzed_text)
    
    logger.info(f"Analysis written to {output_file}")
    return output_file

def create_reel_scripts(input_file: str, output_dir: str, 
                       overlap: int = 2, workers: int = 4, 
                       sections: Optional[str] = None, count: Optional[int] = None,
                       api_key: Optional[str] = None) -> str:
    """Create reel scripts from analyzed text file.
    
    Args:
        input_file: Path to analyzed text file
        output_dir: Directory to save output
        overlap: Number of paragraphs to include from adjacent sections
        workers: Maximum number of parallel workers
        sections: Specific section numbers to process (comma-separated)
        count: Number of reels to generate, starting from the beginning
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the metadata directory
    """
    logger.info("Step 2: Generating reel scripts")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Create generator
    generator = ReelGenerator(
        api_key=api_key,
        output_dir=output_dir,
        overlap_paragraphs=overlap
    )
    
    metadata_dir = os.path.join(output_dir, "metadata")
    
    # Process specific sections if requested
    if sections:
        section_numbers = [int(s.strip()) for s in sections.split(',')]
        
        # Read and parse the text
        text = generator.read_analyzed_text(input_file)
        
        # Split into sections
        sections_list = generator.split_into_sections(text)
        logger.info(f"Split text into {len(sections_list)} sections")
        
        # Extract titles and add context
        titled_sections = generator.extract_section_titles(sections_list)
        all_enriched_sections = generator.add_context_to_sections(titled_sections)
        
        # Filter sections by selected numbers
        enriched_sections = [s for s in all_enriched_sections if s['id'] in section_numbers]
        
        if not enriched_sections:
            logger.error(f"No valid sections found with numbers: {section_numbers}")
            return metadata_dir
            
        logger.info(f"Processing {len(enriched_sections)} selected sections: {section_numbers}")
        
        # Process selected sections in parallel
        processed_sections = generator.process_sections_parallel(enriched_sections, workers)
        
        # Save results
        generator.save_reel_scripts(processed_sections)
        
    elif count:
        # Read and parse the text
        text = generator.read_analyzed_text(input_file)
        
        # Split into sections
        sections_list = generator.split_into_sections(text)
        logger.info(f"Split text into {len(sections_list)} sections")
        
        # Extract titles and add context
        titled_sections = generator.extract_section_titles(sections_list)
        all_enriched_sections = generator.add_context_to_sections(titled_sections)
        
        # Take first N sections
        count = min(count, len(all_enriched_sections))
        enriched_sections = all_enriched_sections[:count]
        
        logger.info(f"Processing first {count} sections")
        
        # Process selected sections in parallel
        processed_sections = generator.process_sections_parallel(enriched_sections, workers)
        
        # Save results
        generator.save_reel_scripts(processed_sections)
    else:
        # Process all sections
        generator.process_file(
            input_filepath=input_file,
            max_workers=workers
        )
    
    logger.info(f"Reel scripts generated and saved to {output_dir}")
    return metadata_dir

def pick_top_reels(metadata_dir: str, top_n: int = 7, api_key: Optional[str] = None) -> str:
    """Select top reels based on viral potential.
    
    Args:
        metadata_dir: Directory containing metadata files
        top_n: Number of top reels to select
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the top reels directory
    """
    logger.info("Step 3: Picking top reels")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Define output directory
    parent_dir = os.path.dirname(metadata_dir)
    top_reels_dir = os.path.join(parent_dir, "top_reels")
    
    # Create output directory path
    Path(top_reels_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading metadata files from {metadata_dir}...")
    metadata_files = load_metadata_files(metadata_dir)
    logger.info(f"Loaded {len(metadata_files)} metadata files.")
    
    logger.info("Analyzing viral potential with Claude API...")
    # Need to set this temporarily because the module is imported
    os.environ["ANTHROPIC_API_KEY"] = api_key
    analyzed_reels = analyze_viral_potential(metadata_files, api_key)
    
    logger.info(f"Selecting top {top_n} viral reels...")
    top_reels = select_top_reels(analyzed_reels, top_n=top_n)
    
    logger.info(f"Saving top reels to {top_reels_dir}...")
    save_top_reels(top_reels, metadata_dir, top_reels_dir)
    
    logger.info("Top reels saved successfully")
    
    # Print summary of top reels
    logger.info("\nTop Viral Reels Summary:")
    for i, reel in enumerate(top_reels, 1):
        score = reel.get('viral_analysis', {}).get('score', 'N/A')
        title = reel.get('title', 'No title')
        filename = reel.get('filename', 'Unknown file')
        logger.info(f"{i}. {filename} - {title} (Score: {score})")
    
    return top_reels_dir

def final_reel_editing(top_reels_dir: str, edit_prompt: str, api_key: Optional[str] = None) -> str:
    """Apply final edits to top reels to improve engagement.
    
    Args:
        top_reels_dir: Directory containing top reels
        edit_prompt: Instructions for editing the reels
        api_key: Anthropic API key (optional)
    
    Returns:
        Path to the final reels directory
    """
    logger.info("Step 4: Final reel editing")
    
    # Use environment variable if not provided
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Get Anthropic client
    client = get_client(api_key)
    
    # Define output directory
    parent_dir = os.path.dirname(top_reels_dir)
    final_reels_dir = os.path.join(parent_dir, "final_reels")
    
    # Create output directory path
    Path(final_reels_dir).mkdir(parents=True, exist_ok=True)
    
    # Hooks to alternate between (from prompt)
    hook_variations = [
        "Это видео для тех, кто...",
        "Это история о том, как...",
        "А вы знали, что...",
        "Вряд ли вы мне поверите, но...",
        "У меня ушло несколько лет, чтобы...",
        "Короче...",
        "Самый классный в мире...",
        "Самый провальный...",
        "Самый лучший...",
        "Самый быстрый...",
        "Самый неэффективный способ..."
    ]
    
    # Load metadata files
    logger.info(f"Loading top reels from {top_reels_dir}...")
    metadata_files = []
    for filename in os.listdir(top_reels_dir):
        if filename.endswith('.json') and not filename.startswith('analysis_'):
            file_path = os.path.join(top_reels_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    metadata_files.append(data)
                    logger.info(f"Loaded {filename}")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    
    for i, reel_data in enumerate(metadata_files):
        # Select a random hook variant for each reel
        hook_variant = random.choice(hook_variations)
        
        # Get the script content
        script = reel_data.get('heygen_script', '')
        title = reel_data.get('title', '')
        
        # Create a prompt for Claude to edit the reel
        system_prompt = "You are an expert at editing social media scripts to maximize engagement. Make edits according to the guidelines provided, while preserving the core message and educational value."
        
        user_prompt = f"""Edit this Instagram reel script to make it more engaging and viral. 

CURRENT SCRIPT:
{script}

TITLE:
{title}

EDITING GUIDELINES:
{edit_prompt}

For this specific reel, use the following hook style:
{hook_variant}

Return ONLY the edited script text without any explanation or additional formatting. The script should be ready to use as-is and in Russian language.
"""
        
        try:
            # Call Claude to edit the script
            logger.info(f"Editing reel {i+1}/{len(metadata_files)}...")
            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1500,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract content as string from the response
            edited_script = response.content[0].text.strip()
            
            # Update the reel data
            reel_data['original_script'] = script
            reel_data['heygen_script'] = edited_script
            
            # Save the edited reel metadata
            output_path = os.path.join(final_reels_dir, f"final_{i+1:02d}_{os.path.basename(reel_data.get('filename', f'reel_{i+1}.json'))}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(reel_data, f, ensure_ascii=False, indent=2)
            
            # Also save as a plain text file for heygen
            heygen_filename = f"final_heygen_{i+1:02d}.txt"
            heygen_path = os.path.join(final_reels_dir, heygen_filename)
            with open(heygen_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n{edited_script}")
            
            logger.info(f"Saved edited reel to {output_path}")
            
        except Exception as e:
            logger.error(f"Error editing reel {i+1}: {str(e)}")
    
    logger.info(f"Final reel editing completed. Edited reels saved to: {final_reels_dir}")
    return final_reels_dir

def main():
    parser = argparse.ArgumentParser(description='Complete workflow for Google Doc to Instagram reels')
    
    # Main options
    parser.add_argument('--url', help='Google Doc URL to analyze')
    parser.add_argument('--service-account-file', help='Path to service account JSON file')
    parser.add_argument('--analyzed-doc', help='Skip step 1 and use this analyzed doc file')
    parser.add_argument('--output-dir', default='output', help='Directory to save all output files')
    parser.add_argument('--api-key', help='Anthropic API key (if not set in env vars)')
    
    # Reel generation options
    parser.add_argument('--overlap', type=int, default=2, help='Number of paragraphs to include from adjacent sections')
    parser.add_argument('--workers', type=int, default=4, help='Maximum number of parallel workers')
    parser.add_argument('--sections', help='Specific section numbers to process (comma-separated, e.g., "1,3,5")')
    parser.add_argument('--count', type=int, help='Number of reels to generate, starting from the beginning')
    
    # Top reel selection
    parser.add_argument('--top-n', type=int, default=7, help='Number of top reels to select (default: 7)')
    parser.add_argument('--metadata-dir', help='Skip steps 1-2 and just select top reels from this directory')
    
    # Final editing options
    parser.add_argument('--edit-prompt', help='Custom prompt for final editing of reels')
    parser.add_argument('--top-reels-dir', help='Directory containing top reels to edit')
    
    # Skip options
    parser.add_argument('--skip-analyze', action='store_true', help='Skip step 1: Google Doc analysis')
    parser.add_argument('--skip-generate', action='store_true', help='Skip step 2: Reel script generation')
    parser.add_argument('--skip-pick', action='store_true', help='Skip step 3: Top reel selection')
    parser.add_argument('--skip-edit', action='store_true', help='Skip step 4: Final reel editing')
    
    args = parser.parse_args()
    
    # Default edit prompt if not provided
    default_edit_prompt = """Убрать: 
- Приветствие (добрый день, привет, и т.д.)
- Представления эксперта (я Сергей Черненко)
- Фразы типа «вот про это мы поговорим в следующем ролике»

Добавить:
- Начать с одного из вариантов цепляющего вступления:
  * «Это видео для тех, кто...» (например: хочет научиться монтировать, но не знает, с чего начать)
  * «Это история о том, как...» (например: я сделал вирусное видео, даже не зная, как монтировать)
  * «А вы знали, что...» (например: можно монтировать видео бесплатно на профессиональном уровне)
  * «Вряд ли вы мне поверите, но...» (например: раньше я боялся монтировать, потому что думал, что это сложно)
  * «У меня ушло несколько лет, чтобы...» (например: понять, как сделать видео, которые набирают миллионы просмотров)
  * Начать со слова «короче» - посыл "сейчас я быстро расскажу"
  * Использовать фразы с превосходными прилагательными: "Самый классный в мире...", "Самый провальный...", "Самый лучший...", "Самый быстрый...", "Самый неэффективный способ..."

Сохранить:
- Основное образовательное содержание
- Ключевые тезисы и рекомендации
- Призыв к действию в конце"""
    
    # Verify API key is available
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("No Anthropic API key provided. Set --api-key or ANTHROPIC_API_KEY environment variable.")
        return
    
    os.environ["ANTHROPIC_API_KEY"] = api_key
    
    # Create output directory
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Analyze Google Doc
    analyzed_doc_path = None
    if not args.skip_analyze and not args.metadata_dir and not args.top_reels_dir:
        if args.analyzed_doc:
            analyzed_doc_path = args.analyzed_doc
            logger.info(f"Using existing analyzed document: {analyzed_doc_path}")
        elif args.url and args.service_account_file:
            try:
                analyzed_doc_path = process_google_doc(args.url, args.service_account_file)
            except Exception as e:
                logger.error(f"Error analyzing Google Doc: {str(e)}")
                return
        else:
            logger.error("For Step 1, you must provide either --analyzed-doc or both --url and --service-account-file")
            return
    
    # Step 2: Generate reel scripts
    metadata_dir = None
    if not args.skip_generate and not args.metadata_dir and not args.top_reels_dir:
        if not analyzed_doc_path and not args.skip_analyze:
            logger.error("Cannot run Step 2 without completing Step 1 or providing --analyzed-doc")
            return
        
        try:
            metadata_dir = create_reel_scripts(
                input_file=analyzed_doc_path,
                output_dir=output_dir,
                overlap=args.overlap,
                workers=args.workers,
                sections=args.sections,
                count=args.count,
                api_key=api_key
            )
        except Exception as e:
            logger.error(f"Error generating reel scripts: {str(e)}")
            return
    elif args.metadata_dir:
        metadata_dir = args.metadata_dir
    
    # Step 3: Pick top reels
    top_reels_dir = None
    if not args.skip_pick and not args.top_reels_dir:
        if not metadata_dir:
            logger.error("Cannot run Step 3 without completing Step 2 or providing --metadata-dir")
            return
        
        try:
            top_reels_dir = pick_top_reels(
                metadata_dir=metadata_dir,
                top_n=args.top_n,
                api_key=api_key
            )
        except Exception as e:
            logger.error(f"Error picking top reels: {str(e)}")
            return
    elif args.top_reels_dir:
        top_reels_dir = args.top_reels_dir
    
    # Step 4: Final reel editing
    if not args.skip_edit:
        if not top_reels_dir:
            logger.error("Cannot run Step 4 without completing Step 3 or providing --top-reels-dir")
            return
        
        edit_prompt = args.edit_prompt if args.edit_prompt else default_edit_prompt
        
        try:
            final_reels_dir = final_reel_editing(
                top_reels_dir=top_reels_dir,
                edit_prompt=edit_prompt,
                api_key=api_key
            )
            logger.info(f"Complete workflow finished. Final reels available at: {final_reels_dir}")
        except Exception as e:
            logger.error(f"Error editing top reels: {str(e)}")
            return
    else:
        if not args.skip_pick:
            logger.info(f"Complete workflow finished. Top reels available at: {top_reels_dir}")
        else:
            logger.info("Complete workflow finished (skipped top reel selection and editing)")

if __name__ == "__main__":
    main() 