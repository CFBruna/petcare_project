"""Service Layer for AI Intelligence - Product Intelligence Agent."""

import json
import time
from dataclasses import dataclass

import structlog
from django.conf import settings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src.apps.ai.embeddings.embeddings_service import EmbeddingsService
from src.apps.ai.embeddings.vector_store import VectorStore
from src.apps.ai.models import AIGeneratedContent, ProductEmbedding
from src.apps.ai.prompts import product_prompts

logger = structlog.get_logger(__name__)


def retry_on_rate_limit(max_retries=3, base_delay=2):
    """Decorator to retry LLM calls on rate limit errors with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles with each retry)
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e)
                    # Check if it's a rate limit error (429 or RESOURCE_EXHAUSTED)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        if attempt < max_retries:
                            delay = base_delay * (2**attempt)  # Exponential backoff
                            logger.warning(
                                "rate_limit_hit_retrying",
                                attempt=attempt + 1,
                                max_retries=max_retries,
                                delay=delay,
                                error=error_str[:200],
                            )
                            time.sleep(delay)
                            continue
                    # Re-raise if not rate limit or max retries exceeded
                    raise
            return None

        return wrapper

    return decorator


@dataclass
class ProductDescriptionRequest:
    """DTO for product description generation request."""

    product_name: str
    category: str | None = None
    brand: str | None = None
    price: float | None = None
    mode: str = "technical"  # "technical" or "creative"


@dataclass
class ProductDescriptionResponse:
    """DTO for product description generation response."""

    description: str
    confidence_score: float
    is_known_product: bool
    similar_products: list[str]
    suggestions: dict[str, str | list[str]]


class ProductIntelligenceService:
    """
    Service Layer for Product Intelligence Agent.

    Responsibilities:
    - Generate product descriptions using LLM + RAG
    - Search for similar products using vector embeddings
    - Detect if product is known or new
    - Generate SEO suggestions
    """

    def __init__(self):
        """Initialize LLM, embeddings, and vector store."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL_NAME,
            temperature=0.7,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        self.embeddings_service = EmbeddingsService()
        self.vector_store = VectorStore(collection_name="products")

    def generate_description(
        self, request: ProductDescriptionRequest, user=None
    ) -> ProductDescriptionResponse:
        """
        Generate product description using RAG + LLM.

        Flow:
        1. Search for similar products (RAG)
        2. Determine if product is known
        3. Generate appropriate description
        4. Generate SEO suggestions
        5. Save for audit
        """
        logger.info(
            "generate_description_started",
            product_name=request.product_name,
            mode=request.mode,
        )

        # 1. Search for similar products
        similar_products = self._search_similar_products(request.product_name)
        is_known = len(similar_products) > 0

        # 2. Generate description
        # 2. Generate description
        if request.mode == "technical":
            description = self._generate_technical_description(
                request, similar_products
            )
            confidence = 0.9 if is_known else 0.7
        else:
            description = self._generate_creative_description(request)
            confidence = 0.7 if is_known else 0.5

        # 3. Generate SEO suggestions
        suggestions = self._generate_seo_suggestions(request, description)

        # 4. Save for audit
        self._save_generated_content(
            request=request,
            description=description,
            confidence=confidence,
            suggestions=suggestions,
            user=user,
        )

        logger.info(
            "generate_description_completed",
            product_name=request.product_name,
            confidence=confidence,
            is_known=is_known,
        )

        return ProductDescriptionResponse(
            description=description,
            confidence_score=confidence,
            is_known_product=is_known,
            similar_products=[p["name"] for p in similar_products[:3]],
            suggestions=suggestions,
        )

    def _search_similar_products(self, product_name: str, top_k: int = 5) -> list[dict]:
        """Search for similar products using embeddings (RAG)."""
        try:
            # Generate embedding for query
            query_embedding = self.embeddings_service.encode(product_name)

            # Search in vector store
            results = self.vector_store.query(
                query_embeddings=[query_embedding], n_results=top_k
            )

            if not results["documents"][0]:
                return []

            similar_products = []
            for i, doc in enumerate(results["documents"][0]):
                similar_products.append(
                    {
                        "name": results["metadatas"][0][i]["name"],
                        "description": doc,
                        "distance": results["distances"][0][i],
                    }
                )

            return similar_products

        except Exception as e:
            logger.error("search_similar_products_failed", error=str(e))
            return []

    @retry_on_rate_limit(max_retries=3, base_delay=2)
    def _generate_technical_description(
        self, request: ProductDescriptionRequest, similar_products: list[dict]
    ) -> str:
        """Generate technical description based on similar products (RAG)."""
        # Build context from similar products
        context = "\n".join(
            [f"- {p['name']}: {p['description']}" for p in similar_products[:3]]
        )

        messages = [
            SystemMessage(content=product_prompts.TECHNICAL_DESCRIPTION_SYSTEM),
            HumanMessage(
                content=product_prompts.TECHNICAL_DESCRIPTION_USER.format(
                    product_name=request.product_name,
                    category=request.category or "Não especificada",
                    brand=request.brand or "Não especificada",
                    price=f"{request.price:.2f}" if request.price else "N/A",
                    similar_products=context,
                )
            ),
        ]

        response = self.llm.invoke(messages)
        return response.content.strip()

    @retry_on_rate_limit(max_retries=3, base_delay=2)
    def _generate_creative_description(self, request: ProductDescriptionRequest) -> str:
        """Generate creative description for new/unknown products."""
        messages = [
            SystemMessage(content=product_prompts.CREATIVE_DESCRIPTION_SYSTEM),
            HumanMessage(
                content=product_prompts.CREATIVE_DESCRIPTION_USER.format(
                    product_name=request.product_name,
                    category=request.category or "Não especificada",
                    brand=request.brand or "Não especificada",
                    price=f"{request.price:.2f}" if request.price else "N/A",
                )
            ),
        ]

        response = self.llm.invoke(messages)
        return response.content.strip()

    @retry_on_rate_limit(max_retries=3, base_delay=2)
    def _generate_seo_suggestions(
        self, request: ProductDescriptionRequest, description: str
    ) -> dict[str, str | list[str]]:
        """Generate SEO suggestions (title, meta, tags, category)."""
        try:
            messages = [
                SystemMessage(content=product_prompts.SEO_SUGGESTIONS_SYSTEM),
                HumanMessage(
                    content=product_prompts.SEO_SUGGESTIONS_USER.format(
                        product_name=request.product_name, description=description
                    )
                ),
            ]

            response = self.llm.invoke(messages)

            # Parse JSON response
            suggestions = json.loads(response.content.strip())
            return suggestions

        except Exception as e:
            logger.error("generate_seo_suggestions_failed", error=str(e))
            return {
                "seo_title": request.product_name,
                "meta_description": description[:160],
                "tags": [],
                "suggested_category": request.category or "",
            }

    def _save_generated_content(
        self,
        request: ProductDescriptionRequest,
        description: str,
        confidence: float,
        suggestions: dict,
        user=None,
    ) -> None:
        """Save generated content for audit and cache."""
        AIGeneratedContent.objects.create(
            content_type="product_description",
            input_data={
                "product_name": request.product_name,
                "category": request.category,
                "brand": request.brand,
                "price": request.price,
                "mode": request.mode,
            },
            generated_content=description,
            model_used=settings.GEMINI_MODEL_NAME,
            confidence_score=confidence,
            created_by=user,
        )

    def index_product(self, product) -> None:
        """
        Index product in vector store for RAG.
        Should be called when product is created/updated.
        """
        logger.info("index_product_started", product_id=product.id)

        try:
            # Generate text for embedding
            text_parts = [product.name]
            if product.description:
                text_parts.append(product.description)
            if product.category:
                text_parts.append(product.category.name)
            if product.brand:
                text_parts.append(product.brand.name)

            text = " ".join(text_parts)

            # Generate embedding
            embedding = self.embeddings_service.encode(text)

            # Check if product already indexed
            try:
                existing = self.vector_store.get(ids=[str(product.id)])
                if existing["ids"]:
                    # Update existing
                    self.vector_store.update(
                        ids=[str(product.id)],
                        embeddings=[embedding],
                        documents=[product.description or ""],
                        metadatas=[
                            {
                                "name": product.name,
                                "category": (
                                    product.category.name if product.category else ""
                                ),
                                "brand": product.brand.name if product.brand else "",
                                "price": float(product.price),
                            }
                        ],
                    )
                else:
                    raise Exception("Not found")
            except Exception:
                # Add new
                self.vector_store.add(
                    ids=[str(product.id)],
                    embeddings=[embedding],
                    documents=[product.description or ""],
                    metadatas=[
                        {
                            "name": product.name,
                            "category": (
                                product.category.name if product.category else ""
                            ),
                            "brand": product.brand.name if product.brand else "",
                            "price": float(product.price),
                        }
                    ],
                )

            # Save embedding in PostgreSQL (for backup)
            ProductEmbedding.objects.update_or_create(
                product=product,
                defaults={
                    "embedding_vector": embedding,
                    "model_version": "all-MiniLM-L6-v2",
                },
            )

            logger.info("index_product_completed", product_id=product.id)

        except Exception as e:
            logger.error("index_product_failed", product_id=product.id, error=str(e))
            raise

    def delete_product_index(self, product_id: int) -> None:
        """Delete product from vector store."""
        try:
            self.vector_store.delete(ids=[str(product_id)])
            logger.info("delete_product_index_completed", product_id=product_id)
        except Exception as e:
            logger.error(
                "delete_product_index_failed", product_id=product_id, error=str(e)
            )
