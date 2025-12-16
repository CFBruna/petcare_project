"""Tests for AI Services - Product Intelligence."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from src.apps.ai.services import (
    ProductDescriptionRequest,
    ProductIntelligenceService,
    retry_on_rate_limit,
)
from src.apps.store.factories import BrandFactory, CategoryFactory, ProductFactory


@pytest.mark.django_db
class TestRetryDecorator:
    """Test retry_on_rate_limit decorator."""

    def test_retry_on_rate_limit_success_first_try(self):
        """Should succeed on first try without retry."""
        call_count = 0

        @retry_on_rate_limit(max_retries=3)
        def mock_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = mock_function()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_rate_limit_429_error(self):
        """Should retry on 429 rate limit error."""
        call_count = 0

        @retry_on_rate_limit(max_retries=2, base_delay=0.1)
        def mock_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("429 RESOURCE_EXHAUSTED")
            return "success"

        result = mock_function()
        assert result == "success"
        assert call_count == 2

    def test_retry_on_rate_limit_max_retries_exceeded(self):
        """Should fail after max retries."""

        @retry_on_rate_limit(max_retries=2, base_delay=0.1)
        def mock_function():
            raise Exception("429 RESOURCE_EXHAUSTED")

        with pytest.raises(Exception, match="429 RESOURCE_EXHAUSTED"):
            mock_function()

    def test_retry_non_rate_limit_error(self):
        """Should not retry on non-rate-limit errors."""
        call_count = 0

        @retry_on_rate_limit(max_retries=3)
        def mock_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Some other error")

        with pytest.raises(ValueError):
            mock_function()
        assert call_count == 1


@pytest.mark.django_db
class TestProductIntelligenceService:
    """Test ProductIntelligenceService."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        with patch("src.apps.ai.services.ChatGoogleGenerativeAI"):
            with patch("src.apps.ai.services.EmbeddingsService"):
                with patch("src.apps.ai.services.VectorStore"):
                    return ProductIntelligenceService()

    @pytest.fixture
    def product_request(self):
        """Create sample product request."""
        return ProductDescriptionRequest(
            product_name="Ração Premium para Cães Adultos 15kg",
            category="Alimentação",
            brand="PremiumPet",
            price=150.0,
            mode="technical",
        )

    def test_generate_description_technical_mode(self, service, product_request):
        """Should generate technical description."""
        # Mock similar products search
        service._search_similar_products = MagicMock(
            return_value=[
                {"name": "Ração Standard 15kg", "description": "Ração balanceada"}
            ]
        )

        # Mock LLM response
        mock_response = AIMessage(
            content="Ração premium elaborada especialmente para cães adultos."
        )
        service.llm.invoke = MagicMock(return_value=mock_response)

        # Mock save
        service._save_generated_content = MagicMock()

        # Execute
        response = service.generate_description(product_request)

        # Assertions
        assert response.description != ""
        assert response.confidence_score > 0.5
        assert response.is_known_product is True
        assert len(response.similar_products) > 0

    def test_generate_description_creative_mode(self, service, product_request):
        """Should generate creative description."""
        product_request.mode = "creative"

        # Mock similar products search
        service._search_similar_products = MagicMock(return_value=[])

        # Mock LLM response
        mock_response = AIMessage(
            content="Transforme a vida do seu melhor amigo com nossa ração premium!"
        )
        service.llm.invoke = MagicMock(return_value=mock_response)

        # Mock save
        service._save_generated_content = MagicMock()

        # Execute
        response = service.generate_description(product_request)

        # Assertions
        assert response.description != ""
        assert response.is_known_product is False
        assert response.confidence_score < 0.9

    def test_search_similar_products_success(self, service):
        """Should search similar products using embeddings."""
        # Mock embeddings
        service.embeddings_service.encode = MagicMock(return_value=[0.1, 0.2, 0.3])

        # Mock vector store results
        service.vector_store.query = MagicMock(
            return_value={
                "documents": [["Ração balanceada para cães"]],
                "metadatas": [[{"name": "Ração Standard"}]],
                "distances": [[0.15]],
            }
        )

        # Execute
        results = service._search_similar_products("Ração Premium")

        # Assertions
        assert len(results) == 1
        assert results[0]["name"] == "Ração Standard"
        assert results[0]["distance"] == 0.15

    def test_search_similar_products_empty(self, service):
        """Should handle empty search results."""
        service.embeddings_service.encode = MagicMock(return_value=[0.1, 0.2])
        service.vector_store.query = MagicMock(
            return_value={"documents": [[]], "metadatas": [[]], "distances": [[]]}
        )

        results = service._search_similar_products("Produto Inexistente")
        assert results == []

    def test_search_similar_products_error(self, service):
        """Should handle search errors gracefully."""
        service.embeddings_service.encode = MagicMock(
            side_effect=Exception("Embedding error")
        )

        results = service._search_similar_products("Test Product")
        assert results == []

    def test_generate_seo_suggestions_success(self, service, product_request):
        """Should generate SEO suggestions."""
        mock_response = AIMessage(
            content='{"seo_title": "Ração Premium Cães 15kg", "meta_description": "Ração completa", "tags": ["ração", "cães"], "suggested_category": "Pet Food"}'
        )
        service.llm.invoke = MagicMock(return_value=mock_response)

        suggestions = service._generate_seo_suggestions(
            product_request, "Test description"
        )

        assert "seo_title" in suggestions
        assert "meta_description" in suggestions
        assert "tags" in suggestions

    def test_generate_seo_suggestions_error(self, service, product_request):
        """Should return fallback SEO on error."""
        service.llm.invoke = MagicMock(side_effect=Exception("LLM Error"))

        suggestions = service._generate_seo_suggestions(
            product_request, "Test description"
        )

        assert suggestions["seo_title"] == product_request.product_name
        assert len(suggestions["meta_description"]) <= 160

    def test_index_product_new(self, service):
        """Should index new product."""
        product = ProductFactory(
            name="Test Product",
            description="Test Description",
            category=CategoryFactory(name="Test Category"),
            brand=BrandFactory(name="Test Brand"),
        )

        # Mock embeddings
        service.embeddings_service.encode = MagicMock(return_value=[0.1, 0.2])

        # Mock vector store - product doesn't exist
        service.vector_store.get = MagicMock(return_value={"ids": []})
        service.vector_store.add = MagicMock()

        # Execute
        service.index_product(product)

        # Assertions
        service.vector_store.add.assert_called_once()
        call_args = service.vector_store.add.call_args
        assert str(product.id) in call_args[1]["ids"]

    def test_index_product_update_existing(self, service):
        """Should update existing product index."""
        product = ProductFactory(name="Test Product")

        service.embeddings_service.encode = MagicMock(return_value=[0.1, 0.2])

        # Mock vector store - product exists
        service.vector_store.get = MagicMock(return_value={"ids": [str(product.id)]})
        service.vector_store.update = MagicMock()

        # Execute
        service.index_product(product)

        # Assertions
        service.vector_store.update.assert_called_once()

    def test_index_product_error(self, service):
        """Should raise error when indexing fails."""
        product = ProductFactory(name="Test Product")

        service.embeddings_service.encode = MagicMock(
            side_effect=Exception("Embedding error")
        )

        with pytest.raises(Exception, match="Embedding error"):
            service.index_product(product)

    def test_delete_product_index(self, service):
        """Should delete product from index."""
        service.vector_store.delete = MagicMock()

        service.delete_product_index(123)

        service.vector_store.delete.assert_called_once_with(ids=["123"])

    def test_save_generated_content(self, service, product_request):
        """Should save generated content for audit."""
        from src.apps.ai.models import AIGeneratedContent

        service._save_generated_content(
            request=product_request,
            description="Test description",
            confidence=0.9,
            suggestions={"seo_title": "Test"},
            user=None,
        )

        content = AIGeneratedContent.objects.last()
        assert content is not None
        assert content.content_type == "product_description"
        assert content.generated_content == "Test description"
        assert content.confidence_score == 0.9
