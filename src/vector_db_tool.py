# vector_db_tool.py
import os
import qdrant_client
from langchain.agents import tool
from langchain.chains import RetrievalQA
from langchain_community.llms import OpenAI
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import OpenAIEmbeddings

def get_vector_store():
    client = qdrant_client.QdrantClient(
        os.getenv("QDRANT_HOST"),
        api_key=os.getenv("QDRANT_API_KEY")
    )
    embeddings = OpenAIEmbeddings()
    vectorstore = Qdrant(
        client=client,
        collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
        embeddings=embeddings
    )
    return vectorstore

class VectorDBToolset:
    def __init__(self):
        # Same approach as in main.py:
        self.vector_store = get_vector_store()
        
        # Build RetrievalQA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=OpenAI(),
            chain_type="stuff",
            retriever=self.vector_store.as_retriever()
        )

    @tool
    def vector_db_query(self, query: str) -> str:
        """
        Query the Qdrant vector store for relevant context
        and get an answer from the LLM.
        """
        return self.qa_chain.run(query)

    def tools(self):
        """Return all the tool methods that Agents can call."""
        return [self.vector_db_query]
