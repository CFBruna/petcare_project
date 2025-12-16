"""Vector store wrapper for ChromaDB."""

from pathlib import Path

import chromadb
from django.conf import settings


class VectorStore:
    """Wrapper for ChromaDB vector database."""

    def __init__(self, collection_name: str = "products"):
        """Initialize ChromaDB client and collection."""
        # Create chroma_db directory if it doesn't exist
        chroma_path = Path(settings.BASE_DIR) / "chroma_db"
        chroma_path.mkdir(exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(chroma_path))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": f"{collection_name} embeddings for RAG"},
        )

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict] | None = None,
    ) -> None:
        """Add embeddings to the collection."""
        self.collection.add(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas  # type: ignore[arg-type]
        )

    def query(self, query_embeddings: list[list[float]], n_results: int = 5) -> dict:  # type: ignore[return]
        """Query similar embeddings."""
        return self.collection.query(  # type: ignore[return-value]
            query_embeddings=query_embeddings, n_results=n_results  # type: ignore[arg-type]
        )

    def update(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict] | None = None,
    ) -> None:
        """Update existing embeddings."""
        self.collection.update(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas  # type: ignore[arg-type]
        )

    def delete(self, ids: list[str]) -> None:
        """Delete embeddings by IDs."""
        self.collection.delete(ids=ids)

    def get(self, ids: list[str]) -> dict:  # type: ignore[return]
        """Get embeddings by IDs."""
        return self.collection.get(ids=ids)  # type: ignore[return-value]

    def count(self) -> int:
        """Get total number of embeddings."""
        return self.collection.count()
