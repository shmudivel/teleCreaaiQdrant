import re
from src.text_analyzer import analyze_text_structure
from src.utils.content_insights import ContentInsightsProcessor

def split_text_into_parts(text, num_parts=4):
    """
    Split raw text into specified number of parts, then analyze structure of each part
    
    Args:
        text (str): The input text to split
        num_parts (int): Number of parts to split the text into (default: 4)
        
    Returns:
        tuple: A tuple containing (analyzed_parts, insights_processor)
    """
    # First, identify semantic sections based on headings and paragraph blocks
    # This helps preserve the original text's logical structure
    semantic_blocks = []
    
    # Find headings (lines that end with colon or have special formatting)
    heading_pattern = re.compile(r'^.{5,100}:[ \t]*$|^[A-ZА-Я\d][A-ZА-Я\d .,:;!?-]{5,100}$', re.MULTILINE)
    heading_matches = list(heading_pattern.finditer(text))
    
    # If no clear headings are found, fall back to paragraph blocks
    if not heading_matches or len(heading_matches) < num_parts - 1:
        # Split by empty lines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Group paragraphs into semantic blocks
        current_block = []
        for para in paragraphs:
            current_block.append(para)
            # Create a new block threshold based on content length and semantics
            if len(''.join(current_block)) > len(text) / (num_parts * 1.5) and len(current_block) >= 2:
                semantic_blocks.append('\n\n'.join(current_block))
                current_block = []
        
        # Add any remaining paragraphs
        if current_block:
            semantic_blocks.append('\n\n'.join(current_block))
    else:
        # Use headings to define semantic blocks
        prev_pos = 0
        for match in heading_matches:
            if match.start() > prev_pos:
                semantic_blocks.append(text[prev_pos:match.start()])
            prev_pos = match.start()
        
        # Add the final block
        if prev_pos < len(text):
            semantic_blocks.append(text[prev_pos:])
    
    # Adjust the blocks to match the desired number of parts
    parts = []
    if len(semantic_blocks) < num_parts:
        # If we have fewer blocks than needed, split the largest blocks
        while len(semantic_blocks) < num_parts:
            # Find the largest block
            largest_idx = max(range(len(semantic_blocks)), key=lambda i: len(semantic_blocks[i]))
            largest_block = semantic_blocks.pop(largest_idx)
            
            # Split the largest block approximately in half, but at a paragraph boundary
            mid_point = len(largest_block) // 2
            paragraph_break = re.search(r'\n\s*\n', largest_block[mid_point:mid_point + 500])
            
            if paragraph_break:
                split_point = mid_point + paragraph_break.start() + 1
            else:
                # Try to find a sentence boundary
                sentence_match = re.search(r'(?<=[.!?])\s+', largest_block[mid_point:mid_point + 200])
                if sentence_match:
                    split_point = mid_point + sentence_match.end()
                else:
                    # Just split at the midpoint as a last resort
                    split_point = mid_point
            
            semantic_blocks.insert(largest_idx, largest_block[:split_point])
            semantic_blocks.insert(largest_idx + 1, largest_block[split_point:])
    
    elif len(semantic_blocks) > num_parts:
        # If we have more blocks than needed, merge smaller adjacent blocks
        while len(semantic_blocks) > num_parts:
            # Find the smallest adjacent pair of blocks
            smallest_pair_idx = min(range(len(semantic_blocks) - 1), 
                                   key=lambda i: len(semantic_blocks[i]) + len(semantic_blocks[i+1]))
            
            # Merge them
            merged_block = semantic_blocks[smallest_pair_idx] + "\n\n" + semantic_blocks[smallest_pair_idx + 1]
            semantic_blocks[smallest_pair_idx] = merged_block
            semantic_blocks.pop(smallest_pair_idx + 1)
    
    # Use the semantic blocks as our parts
    parts = semantic_blocks[:num_parts]
    
    # Make sure we have exactly the number of parts requested
    while len(parts) < num_parts:
        parts.append("")  # Pad with empty strings if needed
    
    # Analyze each part
    analyzed_parts = []
    for i, part in enumerate(parts):
        # Add part marker for reference
        marked_part = f"--- Part {i+1} ---\n{part}"
        analyzed_part = analyze_text_structure(marked_part)
        analyzed_parts.append(analyzed_part)
    
    # Create a content insights processor
    insights_processor = ContentInsightsProcessor(analyzed_parts)
    
    return (analyzed_parts, insights_processor)

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        # Read from file if provided as argument
        with open(sys.argv[1], 'r', encoding='utf-8') as file:
            input_text = file.read()
    else:
        # Otherwise, ask for input
        print("Enter or paste your text (press Ctrl+D on Unix/Linux or Ctrl+Z followed by Enter on Windows to finish):")
        input_text = sys.stdin.read()
    
    # Get number of parts (default to 4)
    num_parts = 4
    if len(sys.argv) > 2:
        try:
            num_parts = int(sys.argv[2])
        except ValueError:
            print(f"Invalid number of parts: {sys.argv[2]}. Using default (4).")
    
    # Split the text
    parts, _ = split_text_into_parts(input_text, num_parts)
    
    # Print or save the parts
    with open("all_parts.txt", 'w', encoding='utf-8') as output_file:
        for i, part in enumerate(parts, 1):
            print(f"\n--- Part {i} ---")
            print(f"Length: {len(part)} characters")
            
            # Write to the combined file with part markers
            output_file.write(f"\n--- Part {i} ---\n")
            output_file.write(part)
            output_file.write("\n")  # Add spacing between parts
            
    print("All parts saved to all_parts.txt") 