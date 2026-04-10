"""
RAG (Retrieval-Augmented Generation) module for LocalScript.

Provides vector database and semantic search capabilities to reduce
hallucinations and improve code generation quality.
"""

from rag.system import RAGSystem, create_rag_system
from rag.knowledge_base import initialize_rag_with_examples, create_knowledge_base_documents
from rag.cache import RAGCache, get_rag_cache

__all__ = [
    "RAGSystem",
    "create_rag_system",
    "initialize_rag_with_examples",
    "create_knowledge_base_documents",
    "RAGCache",
    "get_rag_cache"
]
