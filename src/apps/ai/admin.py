"""Django Admin integration for AI Intelligence."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from src.apps.ai.models import AIGeneratedContent, HealthPattern, ProductEmbedding


@admin.register(AIGeneratedContent)
class AIGeneratedContentAdmin(admin.ModelAdmin):
    """Admin for AI Generated Content with feedback system."""

    list_display = [
        "id",
        "content_type",
        "related_item_link",
        "confidence_badge",
        "acceptance_status",
        "created_at",
        "created_by",
    ]
    list_filter = ["content_type", "was_accepted", "model_used", "created_at"]
    search_fields = ["generated_content", "product__name", "pet__name"]
    readonly_fields = [
        "created_at",
        "model_used",
        "confidence_score",
        "input_data",
        "generated_content_display",
    ]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Content Information",
            {"fields": ("content_type", "product", "pet", "generated_content_display")},
        ),
        (
            "AI Metadata",
            {"fields": ("model_used", "confidence_score", "input_data")},
        ),
        (
            "Feedback",
            {
                "fields": ("was_accepted", "feedback"),
                "description": "Marque como aceito se a descrição foi utilizada. "
                "Adicione feedback para melhorar futuras gerações.",
            },
        ),
        ("Audit", {"fields": ("created_by", "created_at")}),
    )

    def related_item_link(self, obj):
        """Display link to related product or pet."""
        if obj.product:
            return format_html(
                '<a href="/admin/store/product/{}/change/">{}</a>',
                obj.product.id,
                obj.product.name,
            )
        elif obj.pet:
            return format_html(
                '<a href="/admin/pets/pet/{}/change/">{}</a>', obj.pet.id, obj.pet.name
            )
        return "-"

    related_item_link.short_description = "Related Item"

    def confidence_badge(self, obj):
        """Display confidence score with color coding."""
        if obj.confidence_score is None:
            return "-"

        if obj.confidence_score > 0.8:
            color = "#4CAF50"  # Green
        elif obj.confidence_score > 0.6:
            color = "#FF9800"  # Orange
        else:
            color = "#F44336"  # Red

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{:.0%}</span>',
            color,
            obj.confidence_score,
        )

    confidence_badge.short_description = "Confidence"

    def acceptance_status(self, obj):
        """Display acceptance status with icon."""
        if obj.was_accepted:
            return format_html(
                '<span style="color: green; font-size: 16px;">✅ Aceito</span>'
            )
        return format_html(
            '<span style="color: orange; font-size: 16px;">⏳ Pendente</span>'
        )

    acceptance_status.short_description = "Status"

    def generated_content_display(self, obj):
        """Display generated content with formatting."""
        return format_html(
            '<div style="background-color: #f5f5f5; padding: 15px; '
            'border-radius: 5px; max-width: 800px;">'
            '<pre style="white-space: pre-wrap; font-family: inherit;">{}</pre>'
            "</div>",
            obj.generated_content,
        )

    generated_content_display.short_description = "Generated Content"


@admin.register(HealthPattern)
class HealthPatternAdmin(admin.ModelAdmin):
    """Admin for Health Patterns detected by AI."""

    list_display = [
        "id",
        "pet_link",
        "pattern_type",
        "confidence_badge",
        "is_active",
        "last_updated",
    ]
    list_filter = ["pattern_type", "is_active", "confidence_score", "last_updated"]
    search_fields = ["pet__name", "pattern_type", "description"]
    readonly_fields = [
        "first_detected",
        "last_updated",
        "confidence_score",
        "related_records",
        "recommendations_display",
    ]

    fieldsets = (
        ("Pet Information", {"fields": ("pet", "pattern_type")}),
        (
            "Pattern Details",
            {"fields": ("description", "confidence_score", "is_active")},
        ),
        (
            "Recommendations",
            {
                "fields": ("recommendations_display",),
                "description": "AI-generated recommendations based on this pattern",
            },
        ),
        ("Metadata", {"fields": ("related_records", "first_detected", "last_updated")}),
    )

    def pet_link(self, obj):
        """Display link to pet."""
        return format_html(
            '<a href="/admin/pets/pet/{}/change/">{}</a>', obj.pet.id, obj.pet.name
        )

    pet_link.short_description = "Pet"

    def confidence_badge(self, obj):
        """Display confidence score with color coding."""
        if obj.confidence_score > 0.8:
            color = "#4CAF50"
        elif obj.confidence_score > 0.6:
            color = "#FF9800"
        else:
            color = "#F44336"

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{:.0%}</span>',
            color,
            obj.confidence_score,
        )

    confidence_badge.short_description = "Confidence"

    def recommendations_display(self, obj):
        """Display recommendations as formatted list."""
        if not obj.recommendations:
            return "-"

        items = "".join([f"<li>{rec}</li>" for rec in obj.recommendations])
        return format_html(
            '<ul style="margin: 0; padding-left: 20px;">{}</ul>', mark_safe(items)
        )

    recommendations_display.short_description = "Recommendations"


@admin.register(ProductEmbedding)
class ProductEmbeddingAdmin(admin.ModelAdmin):
    """Admin for Product Embeddings (read-only, for debugging)."""

    list_display = ["id", "product_link", "model_version", "updated_at"]
    list_filter = ["model_version", "updated_at"]
    search_fields = ["product__name"]
    readonly_fields = ["product", "embedding_vector", "model_version", "updated_at"]

    def product_link(self, obj):
        """Display link to product."""
        return format_html(
            '<a href="/admin/store/product/{}/change/">{}</a>',
            obj.product.id,
            obj.product.name,
        )

    product_link.short_description = "Product"

    def has_add_permission(self, request):
        """Disable manual creation (auto-generated)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion."""
        return True


# Inline for Product Admin
class AIGeneratedContentInline(admin.TabularInline):
    """Inline to show AI-generated content in Product admin."""

    model = AIGeneratedContent
    extra = 0
    can_delete = False
    readonly_fields = [
        "content_type",
        "generated_content_preview",
        "confidence_score",
        "was_accepted",
        "created_at",
    ]
    fields = [
        "content_type",
        "generated_content_preview",
        "confidence_score",
        "was_accepted",
        "created_at",
    ]

    def generated_content_preview(self, obj):
        """Show preview of generated content."""
        if len(obj.generated_content) > 100:
            return obj.generated_content[:100] + "..."
        return obj.generated_content

    generated_content_preview.short_description = "Content Preview"

    def has_add_permission(self, request, obj=None):
        """Disable manual creation."""
        return False


# Inline for Pet Admin
class HealthPatternInline(admin.TabularInline):
    """Inline to show health patterns in Pet admin."""

    model = HealthPattern
    extra = 0
    can_delete = False
    readonly_fields = [
        "pattern_type",
        "description",
        "confidence_score",
        "is_active",
        "last_updated",
    ]
    fields = ["pattern_type", "description", "confidence_score", "is_active"]

    def has_add_permission(self, request, obj=None):
        """Disable manual creation."""
        return False
