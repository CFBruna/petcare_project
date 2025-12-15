"""URL configuration for AI admin AJAX endpoints."""

from django.urls import path

from src.apps.ai.api.views import (
    analyze_pet_health_ajax,
    generate_product_description_ajax,
)

urlpatterns = [
    path(
        "generate-product-description/",
        generate_product_description_ajax,
        name="generate_product_description_ajax",
    ),
    path(
        "analyze-pet-health/",
        analyze_pet_health_ajax,
        name="analyze_pet_health_ajax",
    ),
]
