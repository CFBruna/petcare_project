"""Tests for AI Embeddings Service and Vector Store."""

from unittest.mock import MagicMock, patch

import pytest

from src.apps.ai.embeddings.embeddings_service import EmbeddingsService
from src.apps.ai.embeddings.vector_store import VectorStore


@pytest.mark.django_db
class TestEmbeddingsService:
    """Test EmbeddingsService."""

    @pytest.fixture
    def service(self):
        """Create embeddings service instance."""
        with patch(
            "src.apps.ai.embeddings.embeddings_service.GoogleGenerativeAIEmbeddings"
        ) as MockEmbeddings:
            mock_instance = MagicMock()
            MockEmbeddings.return_value = mock_instance
            return EmbeddingsService()

    def test_init(self, service):
        """Should initialize with default model."""
        assert service.model_name == "models/text-embedding-004"
        assert service.embeddings is not None

    def test_encode_without_cache(self, service):
        """Should encode text without using cache."""
        service.embeddings.embed_query = MagicMock(return_value=[0.1, 0.2, 0.3])

        embedding = service.encode("Test product", use_cache=False)

        assert embedding == [0.1, 0.2, 0.3]
        service.embeddings.embed_query.assert_called_once_with("Test product")

    def test_encode_with_cache_miss(self, service):
        """Should encode and cache on cache miss."""
        service.embeddings.embed_query = MagicMock(return_value=[0.1, 0.2, 0.3])

        with patch("src.apps.ai.embeddings.embeddings_service.cache") as mock_cache:
            mock_cache.get.return_value = None

            embedding = service.encode("Test product", use_cache=True)

            assert embedding == [0.1, 0.2, 0.3]
            mock_cache.set.assert_called_once()

    def test_encode_with_cache_hit(self, service):
        """Should return cached embedding on cache hit."""
        cached_embedding = [0.5, 0.6, 0.7]

        with patch("src.apps.ai.embeddings.embeddings_service.cache") as mock_cache:
            mock_cache.get.return_value = cached_embedding

            embedding = service.encode("Test product", use_cache=True)

            assert embedding == cached_embedding
            service.embeddings.embed_query.assert_not_called()

    def test_encode_batch_without_cache(self, service):
        """Should encode batch without cache."""
        texts = ["Product 1", "Product 2"]
        expected_embeddings = [[0.1, 0.2], [0.3, 0.4]]

        service.embeddings.embed_documents = MagicMock(return_value=expected_embeddings)

        embeddings = service.encode_batch(texts, use_cache=False)

        assert embeddings == expected_embeddings
        service.embeddings.embed_documents.assert_called_once_with(texts)

    def test_encode_batch_with_partial_cache(self, service):
        """Should use cache for some texts and encode others."""
        texts = ["Product 1", "Product 2", "Product 3"]
        cached_embedding_1 = [0.1, 0.2]
        new_embeddings = [[0.3, 0.4], [0.5, 0.6]]

        with patch("src.apps.ai.embeddings.embeddings_service.cache") as mock_cache:

            def cache_get_side_effect(key):
                if "Product 1" in key or key.endswith(
                    service._get_cache_key("Product 1").split(":")[-1]
                ):
                    return cached_embedding_1
                return None

            mock_cache.get.side_effect = cache_get_side_effect

            service.embeddings.embed_documents = MagicMock(return_value=new_embeddings)

            embeddings = service.encode_batch(texts, use_cache=True)

            assert len(embeddings) == 3
            assert embeddings[0] == cached_embedding_1

    def test_get_cache_key(self, service):
        """Should generate consistent cache keys."""
        text = "Test product"

        key1 = service._get_cache_key(text)
        key2 = service._get_cache_key(text)

        assert key1 == key2
        assert "embedding:" in key1
        assert service.model_name in key1


@pytest.mark.django_db
class TestVectorStore:
    """Test VectorStore."""

    @pytest.fixture
    def vector_store(self):
        """Create vector store instance."""
        with patch("src.apps.ai.embeddings.vector_store.chromadb.PersistentClient"):
            store = VectorStore(collection_name="test_products")
            store.collection = MagicMock()
            return store

    def test_init_creates_directory(self):
        """Should initialize with collection name."""
        with patch("src.apps.ai.embeddings.vector_store.chromadb.PersistentClient"):
            store = VectorStore(collection_name="test")
            assert store.collection is not None

    def test_add_embeddings(self, vector_store):
        """Should add embeddings to collection."""
        ids = ["1", "2"]
        embeddings = [[0.1, 0.2], [0.3, 0.4]]
        documents = ["Doc 1", "Doc 2"]
        metadatas = [{"name": "Product 1"}, {"name": "Product 2"}]

        vector_store.add(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

        vector_store.collection.add.assert_called_once_with(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    def test_query_embeddings(self, vector_store):
        """Should query similar embeddings."""
        query_embeddings = [[0.1, 0.2]]
        expected_results = {
            "documents": [["Similar doc"]],
            "distances": [[0.15]],
            "metadatas": [[{"name": "Similar"}]],
        }

        vector_store.collection.query = MagicMock(return_value=expected_results)

        results = vector_store.query(query_embeddings, n_results=5)

        assert results == expected_results
        vector_store.collection.query.assert_called_once_with(
            query_embeddings=query_embeddings, n_results=5
        )

    def test_update_embeddings(self, vector_store):
        """Should update existing embeddings."""
        ids = ["1"]
        embeddings = [[0.5, 0.6]]
        documents = ["Updated doc"]
        metadatas = [{"name": "Updated Product"}]

        vector_store.update(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

        vector_store.collection.update.assert_called_once_with(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    def test_delete_embeddings(self, vector_store):
        """Should delete embeddings by ID."""
        ids = ["1", "2"]

        vector_store.delete(ids)

        vector_store.collection.delete.assert_called_once_with(ids=ids)

    def test_get_embeddings(self, vector_store):
        """Should get embeddings by ID."""
        ids = ["1", "2"]
        expected_data = {
            "ids": ["1", "2"],
            "embeddings": [[0.1, 0.2], [0.3, 0.4]],
            "documents": ["Doc 1", "Doc 2"],
        }

        vector_store.collection.get = MagicMock(return_value=expected_data)

        result = vector_store.get(ids)

        assert result == expected_data
        vector_store.collection.get.assert_called_once_with(ids=ids)

    def test_count_embeddings(self, vector_store):
        """Should return count of embeddings."""
        vector_store.collection.count = MagicMock(return_value=42)

        count = vector_store.count()

        assert count == 42
        vector_store.collection.count.assert_called_once()
