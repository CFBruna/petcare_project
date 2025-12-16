"""Embeddings service using Google Gemini API (free tier)."""

# MIGRATED FROM sentence-transformers TO Google Gemini Embeddings API
# OLD CODE PRESERVED BELOW AS BACKUP - DELETE AFTER TESTING

import hashlib

from django.conf import settings
from django.core.cache import cache
from langchain_google_genai import GoogleGenerativeAIEmbeddings


class EmbeddingsService:
    """Service for generating embeddings using Google Gemini API.

    Migration Notes:
    - Old: sentence-transformers (all-MiniLM-L6-v2) - ~100 MB download
    - New: Google Gemini text-embedding-004 API - 0 MB, free tier
    - Interface maintained for backward compatibility
    """

    def __init__(self, model_name: str = "models/text-embedding-004"):
        """Initialize the embedding model using Google Gemini API.

        Args:
            model_name: Gemini embedding model (default: text-embedding-004)
        """
        self.model_name = model_name
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=model_name, api_key=settings.GOOGLE_API_KEY
        )

    def encode(self, text: str, use_cache: bool = True) -> list[float]:
        """
        Generate embedding for a single text using Gemini API.

        Args:
            text: Text to encode
            use_cache: Whether to use cache for embeddings

        Returns:
            List of floats representing the embedding
        """
        if use_cache:
            cache_key = self._get_cache_key(text)
            cached_embedding = cache.get(cache_key)
            if cached_embedding is not None:
                return cached_embedding

        # Use Gemini API to generate embedding
        embedding = self.embeddings.embed_query(text)

        if use_cache:
            # Cache for 24 hours
            cache.set(cache_key, embedding, timeout=86400)

        return embedding

    def encode_batch(
        self, texts: list[str], use_cache: bool = True
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts using Gemini API.

        Args:
            texts: List of texts to encode
            use_cache: Whether to use cache for embeddings

        Returns:
            List of embeddings
        """
        if not use_cache:
            # Direct batch encoding via Gemini API
            return self.embeddings.embed_documents(texts)

        embeddings = []
        texts_to_encode = []
        indices_to_encode = []

        # Check cache for each text
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            cached_embedding = cache.get(cache_key)

            if cached_embedding is not None:
                embeddings.append(cached_embedding)
            else:
                embeddings.append(None)
                texts_to_encode.append(text)
                indices_to_encode.append(i)

        # Encode uncached texts via Gemini API
        if texts_to_encode:
            new_embeddings = self.embeddings.embed_documents(texts_to_encode)

            # Update cache and results
            for idx, embedding in zip(indices_to_encode, new_embeddings, strict=False):
                embeddings[idx] = embedding
                cache_key = self._get_cache_key(texts[idx])
                cache.set(cache_key, embedding, timeout=86400)

        return embeddings

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text embedding."""
        # MD5 used only for cache key, not security (Bandit B324)
        text_hash = hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()
        return f"embedding:{self.model_name}:{text_hash}"


# ============================================================================
# OLD CODE - SENTENCE TRANSFORMERS IMPLEMENTATION (BACKUP)
# DELETE AFTER CONFIRMING GEMINI API WORKS
# ============================================================================
#
# from sentence_transformers import SentenceTransformer
# from django.core.cache import cache
# import hashlib
#
#
# class EmbeddingsService:
#     """Service for generating embeddings using Sentence Transformers."""
#
#     def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
#         """Initialize the embedding model."""
#         self.model_name = model_name
#         self.model = SentenceTransformer(model_name)
#
#     def encode(self, text: str, use_cache: bool = True) -> list[float]:
#         """
#         Generate embedding for a single text.
#
#         Args:
#             text: Text to encode
#             use_cache: Whether to use cache for embeddings
#
#         Returns:
#             List of floats representing the embedding
#         """
#         if use_cache:
#             cache_key = self._get_cache_key(text)
#             cached_embedding = cache.get(cache_key)
#             if cached_embedding is not None:
#                 return cached_embedding
#
#         embedding = self.model.encode(text).tolist()
#
#         if use_cache:
#             # Cache for 24 hours
#             cache.set(cache_key, embedding, timeout=86400)
#
#         return embedding
#
#     def encode_batch(
#         self, texts: list[str], use_cache: bool = True
#     ) -> list[list[float]]:
#         """
#         Generate embeddings for multiple texts.
#
#         Args:
#             texts: List of texts to encode
#             use_cache: Whether to use cache for embeddings
#
#         Returns:
#             List of embeddings
#         """
#         if not use_cache:
#             return self.model.encode(texts).tolist()
#
#         embeddings = []
#         texts_to_encode = []
#         indices_to_encode = []
#
#         # Check cache for each text
#         for i, text in enumerate(texts):
#             cache_key = self._get_cache_key(text)
#             cached_embedding = cache.get(cache_key)
#
#             if cached_embedding is not None:
#                 embeddings.append(cached_embedding)
#             else:
#                 embeddings.append(None)
#                 texts_to_encode.append(text)
#                 indices_to_encode.append(i)
#
#         # Encode uncached texts
#         if texts_to_encode:
#             new_embeddings = self.model.encode(texts_to_encode).tolist()
#
#             # Update cache and results
#             for idx, embedding in zip(indices_to_encode, new_embeddings):
#                 embeddings[idx] = embedding
#                 cache_key = self._get_cache_key(texts[idx])
#                 cache.set(cache_key, embedding, timeout=86400)
#
#         return embeddings
#
#     def _get_cache_key(self, text: str) -> str:
#         """Generate cache key for text embedding."""
#         text_hash = hashlib.md5(text.encode()).hexdigest()
#         return f"embedding:{self.model_name}:{text_hash}"
