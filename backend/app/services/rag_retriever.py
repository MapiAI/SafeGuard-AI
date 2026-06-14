# RAG retrieval service.
# Given a query and detected categories, retrieves the most relevant chunks from pgvector.

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector
from app.core.config import settings

CONNECTION_STRING = settings.DATABASE_URL

embeddings = OpenAIEmbeddings(
    api_key=settings.OPENAI_API_KEY,
    model="text-embedding-3-small"
)

vectorstore = PGVector(
    connection_string=CONNECTION_STRING,
    embedding_function=embeddings,
    collection_name="knowledge_base"
)

def retrieve_relevant_docs(message: str, categories: list, k: int = 3) -> str:
    """
    Retrieve the most relevant educational chunks for a given message and categories.
    Returns a single string with all retrieved chunks joined together.
    """
    # Build query combining message content and detected categories
    category_text = ", ".join([c["category"] for c in categories]) if categories else ""
    query = f"{message} {category_text}".strip()

    # Retrieve top-k most similar chunks
    docs = vectorstore.similarity_search(query, k=k)

    if not docs:
        return ""

    # Join chunks with separator
    retrieved = "\n\n---\n\n".join([doc.page_content for doc in docs])
    return retrieved