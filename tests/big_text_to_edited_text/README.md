# Big Text to Edited Text

This set of scripts processes large text documents (like YouTube video scripts) from Google Docs into structured, edited content with topical divisions and timestamped transcripts.

## Features

- Fetches text content directly from Google Docs using a service account
- Analyzes and divides text into distinct topical sections using Claude 3.7
- Splits divided text into separate markdown files
- Creates timestamped transcription for each section

## Setup

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the same directory with the following content:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```
   You can copy the env.example file and update it with your actual API key.

3. Google Docs API authentication:
   - The script uses a service account credentials file located at:
   - `/Users/dahaniglikovdarkhan/Documents/repos/teleCreaaiQdrant/bustling-folio-439811-h8-539f8ab05fa7.json`
   - Make sure this file exists and has the proper permissions

## Usage

Run the main script with a Google Doc ID:

```bash
python main.py --doc_id YOUR_GOOGLE_DOC_ID --output_dir output_directory
```

Where:
- `YOUR_GOOGLE_DOC_ID` is the ID of the Google Doc (found in the URL)
- `output_directory` is the directory where you want to save the processed files

### Example

```bash
python main.py --doc_id 1ABCdefGHIjkLMNopQRStuvWXyz1234567890 --output_dir my_processed_text
```

## Module Functions

The package consists of four main modules:

1. **google_doc_fetcher.py**: Fetches content from Google Docs using a service account
2. **text_analyzer.py**: Analyzes and divides text into distinct topical sections using Claude 3.7
3. **text_splitter.py**: Splits divided text into separate markdown files using Claude 3.7
4. **transcript_creator.py**: Creates timestamped transcription for each section using Claude 3.7

Each module can also be run independently for testing purposes.

## Fallback Mechanisms

If the Claude API calls fail for any reason, the scripts have fallback methods that will still attempt to process the text using rule-based approaches.

For Google Docs, there are two methods:
1. Google Docs API with service account (primary method)
2. Direct export URL for public documents (fallback method, no authentication needed)

## License

This project is open source and available for any use. 