# Script to chunk knowledge base documents and load them into pgvector.
# Run once to index the knowledge base. Re-run if documents are updated.

import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector
from app.core.config import settings

KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "knowledge_base"

CONNECTION_STRING = settings.DATABASE_URL

def load_documents() -> list[dict]:
    """Load all .txt files from the knowledge base directory."""
    documents = []
    for filepath in KNOWLEDGE_BASE_PATH.glob("*.txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        documents.append({
            "content": content,
            "source": filepath.name
        })
        print(f"Loaded: {filepath.name}")
    return documents

def index_knowledge_base():
    """Chunk documents and store embeddings in pgvector."""
    print("Loading documents...")
    documents = load_documents()

    if not documents:
        print("No documents found in knowledge base.")
        return

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " "]
    )

    chunks = []
    metadatas = []
    for doc in documents:
        doc_chunks = splitter.split_text(doc["content"])
        chunks.extend(doc_chunks)
        metadatas.extend([{"source": doc["source"]}] * len(doc_chunks))
        print(f"  {doc['source']} → {len(doc_chunks)} chunks")

    print(f"\nTotal chunks: {len(chunks)}")
    print("Generating embeddings and storing in pgvector...")

    embeddings = OpenAIEmbeddings(
        api_key=settings.OPENAI_API_KEY,
        model="text-embedding-3-small"
    )

    vectorstore = PGVector.from_texts(
        texts=chunks,
        embedding=embeddings,
        metadatas=metadatas,
        connection_string=CONNECTION_STRING,
        collection_name="knowledge_base"
    )

    print(f"Done. {len(chunks)} chunks indexed in pgvector.")
    return vectorstore

if __name__ == "__main__":
    index_knowledge_base()