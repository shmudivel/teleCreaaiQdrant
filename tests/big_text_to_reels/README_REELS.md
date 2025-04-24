# Instagram Reel Script Generator

cd tests/big_text_to_reels && python create_reel_scripts.py --input analyzed_text.txt --output ../../reels_output --sections "9"

Perfect! I've successfully modified the script to support two new ways to generate reels:
Creating specific reels using the --sections parameter:
Apply to README_REELS...
Run

   python create_reel_scripts.py --input analyzed_text.txt --output reels_output --sections "1,5,9"

"
This generates reels only for the specified section numbers (in this example, sections 1, 5, and 9).
Creating a specific number of reels using the --count parameter:
Apply to README_REELS...
Run

   python create_reel_scripts.py --input analyzed_text.txt --output reels_output --count 3

3
This generates the first N reels (in this example, the first 3 sections).
The command successfully generated 3 reel scripts in the reels_output/reels directory. Each script includes:
The main reel script text
A catchy description for the Instagram post
Relevant hashtags
Key talking points for the content
Visual suggestions for creating the reel
You can now use either option to control exactly how many reels you want to generate without having to process the entire document.



This tool transforms analyzed text into engaging, ready-to-use Instagram reel scripts. It handles all aspects of the process from dividing long text into meaningful sections to generating optimized scripts for each section.

## Features

- **Semantic Division** - Works with text that has already been divided into logical sections by topic (using divider lines)
- **Contextual Awareness** - Includes content from adjacent sections for better continuity
- **Parallel Processing** - Processes multiple sections simultaneously for faster results
- **Improved Quality** - Models perform better on smaller, focused text segments
- **Enhanced Transitions** - Optional second pass ensures smooth flow between reels
- **Complete Reel Package** - Creates not just scripts but also descriptions, hashtags, talking points, and visual suggestions

## Prerequisites

- Python 3.7+
- Anthropic API key (Claude model)
- Previously analyzed text with topic dividers (created using `analyze_google_doc.py`)

## Installation

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Set up your Anthropic API key:
   - Option 1: Create a `.env` file in the project root with:
     ```
     ANTHROPIC_API_KEY=your_api_key_here
     ```
   - Option 2: Pass it directly via command line argument

## Usage

Run the script with the following command:

```bash
python create_reel_scripts.py --input analyzed_text.txt --output reels_output
```

### Command-line Arguments

- `--input`: Path to the analyzed text file (required)
- `--output`: Directory to save output files (default: 'output')
- `--api-key`: Anthropic API key (optional if in .env file)
- `--overlap`: Number of paragraphs to include from adjacent sections (default: 2)
- `--no-second-pass`: Skip the second pass for transition improvements
- `--workers`: Maximum number of parallel workers (default: 4)

## Output

The script creates two directories:

1. `reels/`: Contains plain text files with reel scripts and metadata:
   - Script text
   - Post description
   - Hashtags
   - Talking points
   - Visual suggestions

2. `metadata/`: Contains JSON files with all generated data for each section

## Workflow Example

1. First, use `analyze_google_doc.py` to get text with topic dividers:
   ```bash
   python analyze_google_doc.py --url "https://docs.google.com/document/d/YOUR_DOC_ID/edit" --service-account-file "path/to/credentials.json" --output "analyzed_text.txt"
   ```

2. Then, generate reel scripts from the analyzed text:
   ```bash
   python create_reel_scripts.py --input analyzed_text.txt --output reels_output
   ```

3. Review the generated scripts in the `reels_output/reels` directory

4. Use these scripts to create Instagram reels

## How It Works

1. The text is split into sections based on divider lines
2. Section titles are extracted
3. Overlapping context from adjacent sections is added
4. Claude AI transforms each section into a reel script
5. Optional second pass to improve transitions between sections
6. Results are saved as formatted text files and JSON metadata 