import re
from src.text_analyzer import analyze_text_structure

def split_text_into_parts(text, num_parts=4):
    """
    Split analyzed text STRUCTURE into specified number of parts
    """
    # Get analyzed structure first
    structure = analyze_text_structure(text)
    print(f"Analyzed text structure:\n{structure}\n")
    
    # Split the structure text instead of original
    total_length = len(structure)
    part_length = total_length // num_parts
    
    parts = []
    start_index = 0
    
    for i in range(num_parts - 1):
        end_index = start_index + part_length
        
        if end_index >= total_length:
            break
        
        # Find natural breaks in structure (section numbers)
        # Look for the next section header
        next_section = re.search(r'\n\d+\. ', structure[end_index:])
        if next_section:
            end_index += next_section.start()
        
        parts.append(structure[start_index:end_index])
        start_index = end_index
    
    parts.append(structure[start_index:])
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