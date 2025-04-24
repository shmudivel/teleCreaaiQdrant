# Google Doc to Instagram Reels Workflow

This tool automates the process of turning Google Doc content into engaging Instagram reels scripts, with viral potential analysis.

## Overview

The workflow consists of three main steps:

1. **Google Doc Analysis**: Extracts content from a Google Doc and divides it into logical sections
2. **Reel Script Generation**: Creates Instagram reel scripts for each section with Claude AI
3. **Top Reel Selection**: Analyzes and scores each reel for viral potential, selecting the best ones

## Prerequisites

- Python 3.7+
- Anthropic API key for Claude
- Google service account with access to Google Docs API

## Installation

1. Install required dependencies:

```bash
pip install google-auth google-api-python-client anthropic python-dotenv
```

2. Set up environment variables:

Create a file named `.env` in this directory with:

```
ANTHROPIC_API_KEY=your_anthropic_api_key
```

3. Create a Google service account and download the JSON key file

## Usage

### Complete Workflow

Run the entire workflow from Google Doc to top reels selection:

```bash
python complete_reel_workflow.py --url "https://docs.google.com/document/d/your-doc-id" --service-account-file "path/to/service-account.json" --output-dir "output"
```

### Options

- `--url`: Google Doc URL to analyze
- `--service-account-file`: Path to Google service account JSON file
- `--output-dir`: Directory to save all output files (default: "output")
- `--api-key`: Anthropic API key (if not set in .env file)
- `--overlap`: Number of paragraphs to include from adjacent sections (default: 2)
- `--workers`: Maximum number of parallel workers (default: 4)
- `--sections`: Specific section numbers to process (e.g., "1,3,5")
- `--count`: Number of reels to generate, starting from the beginning
- `--top-n`: Number of top reels to select (default: 10)

### Running Specific Steps

You can also run specific parts of the workflow:

#### Start with an already analyzed document:

```bash
python complete_reel_workflow.py --analyzed-doc "path/to/analyzed_doc.txt" --output-dir "output" --skip-analyze
```

#### Only pick top reels from existing metadata:

```bash
python complete_reel_workflow.py --metadata-dir "path/to/metadata/dir" --output-dir "output" --skip-analyze --skip-generate
```

#### Skip the top reel selection step:

```bash
python complete_reel_workflow.py --url "https://docs.google.com/document/d/your-doc-id" --service-account-file "path/to/service-account.json" --output-dir "output" --skip-pick
```

## Output Structure

The workflow produces the following directory structure:

```
output/
├── analyzed_doc_*.txt       # Analyzed document with section dividers
├── metadata/                # JSON metadata for each reel
│   ├── metadata_01.json
│   └── ...
├── reels/                   # HeyGen script files for each reel
│   ├── heygen_01_of_XX_*.txt
│   └── ...
└── top_reels/               # Selected top reels with analysis
    ├── metadata_01.json
    ├── analysis_metadata_01.json
    └── ...
```

## Example

```bash
# Full workflow
python complete_reel_workflow.py --url "https://docs.google.com/document/d/1abc123def456" --service-account-file "service-account.json" --output-dir "my_project"

# Generate only 5 reels from the beginning
python complete_reel_workflow.py --url "https://docs.google.com/document/d/1abc123def456" --service-account-file "service-account.json" --output-dir "my_project" --count 5

# Process specific sections
python complete_reel_workflow.py --url "https://docs.google.com/document/d/1abc123def456" --service-account-file "service-account.json" --output-dir "my_project" --sections "2,4,6,8"
``` 