import os
import logging
from typing import Optional, List, Dict, Any, Tuple
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.llm_config import get_embeddings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "clinixai_reports"
_vector_store: Optional[Chroma] = None


def get_vector_store() -> Chroma:
    """
    Returns the singleton Chroma vector store instance.
    Uses GoogleGenerativeAIEmbeddings when GEMINI_API_KEY is available,
    otherwise falls back to Chroma's built-in embedding function.
    """
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    embeddings = get_embeddings()

    _vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIR,
    )
    return _vector_store


def index_report(
    user_id: int,
    report_id: int,
    filename: str,
    pages_text: List[Tuple[int, str]],
) -> int:
    """
    Chunks and indexes a medical report page by page into the Chroma vector store.
    pages_text: list of (page_number, text) tuples.
    Returns: number of chunks indexed.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=120,
        separators=["\n\n", "\n", "; ", ". ", " ", ""],
    )

    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    ids: List[str] = []

    for page_num, page_content in pages_text:
        content = page_content.strip()
        if not content:
            continue

        page_chunks = splitter.split_text(content)
        for chunk_idx, chunk in enumerate(page_chunks):
            chunk_id = f"user_{user_id}_rep_{report_id}_p{page_num}_c{chunk_idx}"
            texts.append(chunk)
            metadatas.append({
                "user_id": user_id,
                "report_id": report_id,
                "filename": filename,
                "page": page_num,
                "chunk_idx": chunk_idx,
            })
            ids.append(chunk_id)

    if not texts:
        return 0

    vs = get_vector_store()
    vs.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    logger.info(
        f"Indexed {len(texts)} chunks for report '{filename}' (ID: {report_id}, User: {user_id})"
    )
    return len(texts)


def delete_report_vectors(user_id: int, report_id: int) -> None:
    """
    Deletes all vectors belonging to a specific report of a user.
    """
    vs = get_vector_store()
    try:
        vs._collection.delete(where={"$and": [{"user_id": user_id}, {"report_id": report_id}]})
    except Exception as e:
        logger.warning(f"Error deleting vectors for report {report_id}: {e}")


def retrieve_relevant_chunks(
    user_id: int,
    query: str,
    top_k: Optional[int] = None,
    report_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieves the most semantically relevant chunks for a user's query.
    Enforces user_id multi-tenancy boundary.
    """
    vs = get_vector_store()
    k = top_k or settings.RAG_TOP_K

    if report_id:
        filter_dict = {"$and": [{"user_id": user_id}, {"report_id": report_id}]}
    else:
        filter_dict = {"user_id": user_id}

    try:
        results = vs.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter_dict,
        )
    except Exception as e:
        logger.warning(f"similarity_search_with_score failed: {e}")
        try:
            docs = vs.similarity_search(query=query, k=k, filter=filter_dict)
            results = [(doc, 1.0) for doc in docs]
        except Exception as inner_e:
            logger.error(f"Vector search failed: {inner_e}")
            return []

    chunks = []
    for doc, dist in results:
        meta = doc.metadata or {}
        filename = meta.get("filename", "Report")
        page = meta.get("page", 1)
        # Normalize distance into a 0.0 - 1.0 similarity score
        score = round(1.0 / (1.0 + float(dist)), 3) if dist is not None else 1.0

        chunks.append({
            "text": doc.page_content,
            "filename": filename,
            "page": page,
            "report_id": meta.get("report_id"),
            "score": score,
            "distance": round(float(dist), 3) if dist is not None else None,
            "citation": f"{filename} (Page {page})",
        })

    return chunks


def format_rag_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Formats retrieved chunks into clean markdown text with source labels.
    """
    if not chunks:
        return ""

    formatted = []
    for i, c in enumerate(chunks, start=1):
        formatted.append(
            f"--- Document Excerpt [{i}] (Source: {c['citation']}) ---\n{c['text']}"
        )
    return "\n\n".join(formatted)

