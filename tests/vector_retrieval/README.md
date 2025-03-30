# Qdrant Vector DB Retrieval Test

This test demonstrates how to retrieve information from a Qdrant vector database using LangChain and OpenAI.

## What This Test Does

The test specifically retrieves data from the `context-main3` collection in Qdrant using:

- Qdrant Client for connecting to the vector database
- LangChain for the retrieval pipeline
- OpenAI for embeddings and LLM capabilities

The test includes two test cases:
1. `test_simple_retrieval`: Tests retrieval using a general prompt
2. `test_specific_retrieval`: Tests retrieval using a more specific prompt

## Requirements

Make sure the following environment variables are set in your `.env` file:
- `QDRANT_HOST`: The URL of your Qdrant instance
- `QDRANT_API_KEY`: Your Qdrant API key
- `OPENAI_API_KEY`: Your OpenAI API key

## Running the Test

Run the test with:

```bash
python -m unittest tests/vector_retrieval/test_qdrant_retrieval.py
```

Or directly execute the script:

```bash
python tests/vector_retrieval/test_qdrant_retrieval.py
```

## Expected Output

The test will print the prompts and responses from the vector database retrieval for each test case. Each response will be based on the information stored in the `context-main3` collection.

## Customizing the Test

You can modify the test prompts in the test methods to retrieve different types of information from your vector database. 