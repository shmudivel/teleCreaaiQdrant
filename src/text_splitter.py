import re

def split_text_into_parts(text, num_parts=4):
    """
    Split a large text into a specified number of roughly equal parts.
    """
    # Calculate the approximate length of each part
    total_length = len(text)
    part_length = total_length // num_parts
    
    parts = []
    start_index = 0
    
    for i in range(num_parts - 1):
        # Find the nearest space or newline after the calculated part length
        end_index = start_index + part_length
        
        # Adjust end_index to avoid splitting words/sentences
        if end_index < total_length:
            # First try to find sentence boundaries
            substring = text[end_index:]
            # Look for punctuation followed by whitespace or end of string
            match = re.search(r'(?<=[.!?])\s+', substring)
            if match:
                end_index += match.end()  # Split after punctuation and whitespace
            else:
                # Try to find a newline first
                newline_pos = text.find('\n', end_index)
                space_pos = text.find(' ', end_index)
                
                if newline_pos != -1 and (space_pos == -1 or newline_pos < space_pos):
                    end_index = newline_pos + 1
                elif space_pos != -1:
                    end_index = space_pos + 1
        
        # Add the part to our list
        parts.append(text[start_index:end_index])
        start_index = end_index
    
    # Add the last part (remaining text)
    parts.append(text[start_index:])
    
    return parts 