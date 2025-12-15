"""AJAX views for AI admin integration."""

import json

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from src.apps.ai.agents.health_agent import (
    HealthAssistantService,
    HealthInsightRequest,
)
from src.apps.ai.services import ProductDescriptionRequest, ProductIntelligenceService


@staff_member_required
@require_POST
def generate_product_description_ajax(request):
    """AJAX endpoint to generate product description."""
    try:
        data = json.loads(request.body)

        product_name = data.get("product_name")
        category = data.get("category")
        brand = data.get("brand")
        price = data.get("price")
        mode = data.get("mode", "technical")

        if not product_name:
            return JsonResponse({"success": False, "error": "Product name is required"})

        # Generate description
        service = ProductIntelligenceService()
        request_dto = ProductDescriptionRequest(
            product_name=product_name,
            category=category,
            brand=brand,
            price=float(price) if price else None,
            mode=mode,
        )

        result = service.generate_description(request_dto, user=request.user)

        return JsonResponse(
            {
                "success": True,
                "description": result.description,
                "confidence_score": result.confidence_score,
                "is_known_product": result.is_known_product,
                "similar_products": result.similar_products,
                "suggestions": result.suggestions,
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@staff_member_required
@require_POST
def analyze_pet_health_ajax(request):
    """AJAX endpoint to analyze pet health."""
    try:
        data = json.loads(request.body)
        pet_id = data.get("pet_id")

        if not pet_id:
            return JsonResponse({"success": False, "error": "Pet ID is required"})

        # Analyze health
        service = HealthAssistantService()
        request_dto = HealthInsightRequest(pet_id=int(pet_id), analysis_period_days=180)

        result = service.analyze_pet_health(request_dto, user=request.user)

        # Convert patterns to dict
        patterns_data = []
        for pattern in result.patterns:
            patterns_data.append(
                {
                    "pattern_type": pattern.get("pattern_type", ""),
                    "description": pattern.get("description", ""),
                    "confidence_score": pattern.get("confidence_score", 0),
                }
            )

        return JsonResponse(
            {
                "success": True,
                "health_score": result.health_score,
                "patterns": patterns_data,
                "alerts": result.alerts,
                "recommendations": result.recommendations,
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
