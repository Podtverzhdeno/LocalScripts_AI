"""
RAG (Retrieval-Augmented Generation) system for LocalScript.

Reduces hallucinations by retrieving relevant Lua code examples and documentation
before generating code. Improves speed by caching embeddings.

Architecture:
- ChromaDB for vector storage (local, no server needed)
- Sentence-transformers for embeddings (fast, local)
- Knowledge base: Lua examples, patterns, best practices
"""

from pathlib import Path
from typing import List, Dict, Optional
import logging

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

logger = logging.getLogger("localscript.rag")

# Global cache for embedding model (avoid reloading on every RAG init)
_EMBEDDING_MODEL_CACHE = {}


class RAGSystem:
    """
    RAG system for code generation.

    Features:
    - Fast local embeddings (sentence-transformers)
    - Persistent vector store (ChromaDB)
    - Semantic search for relevant examples
    - Caching for speed
    """

    def __init__(
        self,
        persist_directory: str = ".veai/chroma",
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "lua_knowledge"
    ):
        """
        Initialize RAG system.

        Args:
            persist_directory: Where to store ChromaDB data
            embedding_model: HuggingFace model for embeddings (default: fast & small)
            collection_name: ChromaDB collection name
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing RAG with model: {embedding_model}")

        # Check if embedding model is already cached
        if embedding_model in _EMBEDDING_MODEL_CACHE:
            logger.info(f"Using cached embedding model: {embedding_model}")
            self.embeddings = _EMBEDDING_MODEL_CACHE[embedding_model]
        else:
            # Initialize embeddings (local, fast) - only once per model
            logger.info(f"Loading embedding model (first time): {embedding_model}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': 'cpu'},  # Use GPU if available: 'cuda'
                encode_kwargs={'normalize_embeddings': True}
            )
            # Cache for future use
            _EMBEDDING_MODEL_CACHE[embedding_model] = self.embeddings
            logger.info(f"Embedding model cached for future use")

        # Initialize vector store
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.persist_directory)
        )

        logger.info(f"RAG initialized. Documents in store: {self.vectorstore._collection.count()}")

    def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the knowledge base.

        Args:
            documents: List of LangChain Document objects
        """
        if not documents:
            return

        logger.info(f"Adding {len(documents)} documents to RAG")
        self.vectorstore.add_documents(documents)
        logger.info(f"Total documents: {self.vectorstore._collection.count()}")

    def add_code_example(
        self,
        code: str,
        description: str,
        category: str = "general",
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Add a Lua code example to the knowledge base.

        Args:
            code: Lua code snippet
            description: What this code does
            category: Category (e.g., "algorithm", "pattern", "stdlib")
            metadata: Additional metadata
        """
        meta = metadata or {}
        meta.update({
            "category": category,
            "type": "code_example"
        })

        # Combine description and code for better retrieval
        content = f"{description}\n\n```lua\n{code}\n```"

        doc = Document(
            page_content=content,
            metadata=meta
        )

        self.add_documents([doc])

    def retrieve(
        self,
        query: str,
        k: int = 3,
        filter_dict: Optional[Dict] = None
    ) -> List[Document]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Search query (task description)
            k: Number of results to return
            filter_dict: Metadata filters (e.g., {"category": "algorithm"})

        Returns:
            List of relevant documents
        """
        logger.debug(f"Retrieving {k} documents for query: {query[:100]}...")

        if filter_dict:
            results = self.vectorstore.similarity_search(
                query,
                k=k,
                filter=filter_dict
            )
        else:
            results = self.vectorstore.similarity_search(query, k=k)

        logger.debug(f"Retrieved {len(results)} documents")
        return results

    def retrieve_with_scores(
        self,
        query: str,
        k: int = 3,
        score_threshold: float = 0.5
    ) -> List[tuple[Document, float]]:
        """
        Retrieve documents with similarity scores.

        Args:
            query: Search query
            k: Number of results
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of (document, score) tuples
        """
        results = self.vectorstore.similarity_search_with_score(query, k=k)

        # Filter by threshold
        filtered = [(doc, score) for doc, score in results if score >= score_threshold]

        logger.debug(f"Retrieved {len(filtered)}/{len(results)} documents above threshold {score_threshold}")
        return filtered

    def format_context(self, documents: List[Document], max_length: int = 2000) -> str:
        """
        Format retrieved documents as context for LLM.

        Args:
            documents: Retrieved documents
            max_length: Maximum context length in characters

        Returns:
            Formatted context string
        """
        if not documents:
            return ""

        context_parts = ["Relevant examples from knowledge base:\n"]
        current_length = len(context_parts[0])

        for i, doc in enumerate(documents, 1):
            part = f"\nExample {i}:\n{doc.page_content}\n"

            if current_length + len(part) > max_length:
                break

            context_parts.append(part)
            current_length += len(part)

        return "".join(context_parts)

    def clear(self) -> None:
        """Clear all documents from the knowledge base."""
        logger.warning("Clearing all documents from RAG")

        # Store collection name before deletion
        collection_name = self.vectorstore._collection.name

        # Delete collection
        self.vectorstore.delete_collection()

        # Reinitialize with reset_collection
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.persist_directory)
        )
        self.vectorstore.reset_collection()

    def get_stats(self) -> Dict:
        """Get statistics about the knowledge base."""
        count = self.vectorstore._collection.count()
        return {
            "total_documents": count,
            "embedding_model": self.embeddings.model_name,
            "persist_directory": str(self.persist_directory)
        }


def create_rag_system(config: Optional[Dict] = None) -> RAGSystem:
    """
    Factory function to create RAG system with config.

    Args:
        config: Configuration dict (from settings.yaml)

    Returns:
        Initialized RAGSystem
    """
    config = config or {}

    return RAGSystem(
        persist_directory=config.get("persist_directory", ".veai/chroma"),
        embedding_model=config.get("embedding_model", "all-MiniLM-L6-v2"),
        collection_name=config.get("collection_name", "lua_knowledge")
    )
