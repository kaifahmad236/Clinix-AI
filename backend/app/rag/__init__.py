"""
RAG (Retrieval-Augmented Generation) package for ClinixAI.
Provides document chunking, vector indexing, and semantic retrieval for medical reports.
"""

from app.rag.vector_store import (
    index_report,
    delete_report_vectors,
    retrieve_relevant_chunks,
    format_rag_context,
)

__all__ = [
    "index_report",
    "delete_report_vectors",
    "retrieve_relevant_chunks",
    "format_rag_context",
]

