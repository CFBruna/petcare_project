from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models


class AIGeneratedContent(models.Model):
    """Stores AI-generated content for audit and cache purposes."""

    CONTENT_TYPE_CHOICES = [
        ("product_description", "Product Description"),
        ("product_title", "Product Title"),
        ("health_insight", "Health Insight"),
        ("health_alert", "Health Alert"),
    ]

    content_type = models.CharField(max_length=50, choices=CONTENT_TYPE_CHOICES)
    input_data = models.JSONField(verbose_name="Input Data")
    generated_content = models.TextField(verbose_name="Generated Content")
    model_used = models.CharField(max_length=100, default="gemini-2.5-flash")
    confidence_score = models.FloatField(null=True, blank=True)
    was_accepted = models.BooleanField(default=False, verbose_name="Accepted by User")
    feedback = models.TextField(blank=True, verbose_name="User Feedback")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Relationships
    product = models.ForeignKey(
        "store.Product",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ai_contents",
    )
    pet = models.ForeignKey(
        "pets.Pet",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ai_insights",
    )

    class Meta:
        verbose_name = "AI Generated Content"
        verbose_name_plural = "AI Generated Contents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_type", "created_at"]),
            models.Index(fields=["product", "content_type"]),
            models.Index(fields=["pet", "content_type"]),
        ]

    def __str__(self):
        return f"{self.get_content_type_display()} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"


class ProductEmbedding(models.Model):
    """Stores product embeddings for vector search (RAG)."""

    product = models.OneToOneField(
        "store.Product", on_delete=models.CASCADE, related_name="embedding"
    )
    embedding_vector = ArrayField(
        models.FloatField(),
        size=384,  # all-MiniLM-L6-v2 embedding size
        verbose_name="Embedding Vector",
    )
    model_version = models.CharField(max_length=100, default="all-MiniLM-L6-v2")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product Embedding"
        verbose_name_plural = "Product Embeddings"

    def __str__(self):
        return f"Embedding: {self.product.name}"


class HealthPattern(models.Model):
    """Stores detected health patterns for pets."""

    pet = models.ForeignKey(
        "pets.Pet", on_delete=models.CASCADE, related_name="health_patterns"
    )
    pattern_type = models.CharField(
        max_length=100,
        verbose_name="Pattern Type",
        help_text="e.g., 'seasonal_allergy', 'recurring_infection'",
    )
    description = models.TextField(verbose_name="Pattern Description")
    confidence_score = models.FloatField(verbose_name="Confidence Score")
    first_detected = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    related_records = models.JSONField(
        default=list,
        verbose_name="Related Health Records",
        help_text="IDs of health records that contributed to this pattern",
    )
    recommendations = models.JSONField(
        default=list,
        verbose_name="AI Recommendations",
        help_text="Suggested actions based on this pattern",
    )

    class Meta:
        verbose_name = "Health Pattern"
        verbose_name_plural = "Health Patterns"
        ordering = ["-last_updated"]

    def __str__(self):
        return f"{self.pet.name} - {self.pattern_type}"
