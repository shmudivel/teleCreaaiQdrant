import re
from src.text_analyzer import analyze_text_structure

def split_text_into_parts(text, num_parts=4):
    """
    Split a large text into a specified number of roughly equal parts.
    """
    # First analyze text structure
    structure = analyze_text_structure(text)
    print(f"Analyzed text structure:\n{structure}\n")
    
    # Calculate the approximate length of each part
    total_length = len(text)
    part_length = total_length // num_parts
    
    parts = []
    start_index = 0
    
    for i in range(num_parts - 1):
        # Find the nearest space or newline after the calculated part length
        end_index = start_index + part_length
        
        # Make sure we don't exceed the text length
        if end_index >= total_length:
            break
        
        # Try to find a good breaking point (end of sentence, paragraph, etc.)
        # First, look for a paragraph break
        newline_pos = text.find('\n\n', end_index - 100, end_index + 100)
        
        if newline_pos != -1:
            end_index = newline_pos + 2
        else:
            # Look for end of sentence
            period_pos = text.find('. ', end_index - 100, end_index + 100)
            
            if period_pos != -1:
                end_index = period_pos + 2
            else:
                # Just find the nearest space
                space_pos = text.find(' ', end_index)
                
                if space_pos != -1:
                    end_index = space_pos + 1
        
        # Add the part to our list
        parts.append(text[start_index:end_index])
        start_index = end_index
    
    # Add the last part (remaining text)
    parts.append(text[start_index:])
    
    return parts

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
    parts = split_text_into_parts(input_text, num_parts)
    
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