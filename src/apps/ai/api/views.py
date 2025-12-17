import json

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.ai.agents.health_agent import (
    HealthAssistantService,
    HealthInsightRequest,
)
from src.apps.ai.agents.scheduling_agent import (
    SchedulingAgentService,
    SchedulingIntentRequest,
)
from src.apps.ai.api.serializers import (
    SchedulingIntentRequestSerializer,
    SchedulingIntentResponseSerializer,
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

        service = HealthAssistantService()
        request_dto = HealthInsightRequest(pet_id=int(pet_id), analysis_period_days=180)

        result = service.analyze_pet_health(request_dto, user=request.user)

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


class ScheduleIntentView(APIView):
    """AI-powered scheduling intent generation from natural language.

    This endpoint uses Google Gemini with Function Calling to interpret
    appointment booking requests and execute real database queries.
    """

    @extend_schema(
        request=SchedulingIntentRequestSerializer,
        responses={200: SchedulingIntentResponseSerializer},
        examples=[
            OpenApiExample(
                "Complete booking request",
                value={
                    "user_input": "Preciso banho e tosa para meu Golden Retriever de 5 anos, de preferência sábado de manhã",
                    "customer_id": 1,
                },
                request_only=True,
            ),
            OpenApiExample(
                "Check availability only",
                value={
                    "user_input": "Quais horários disponíveis no sábado?",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Successful response",
                value={
                    "message": "Encontrei o Thor! Temos 3 horários disponíveis no sábado de manhã: 09:00, 10:30 e 11:00. O banho e tosa para porte grande custa R$ 120,00 e leva cerca de 90 minutos. Qual horário prefere?",
                    "tools_executed": [
                        {
                            "tool_name": "search_customer_pets",
                            "arguments": {
                                "species": "dog",
                                "breed": "golden retriever",
                                "age_min": 5,
                                "age_max": 5,
                            },
                            "result": [
                                {
                                    "id": 1,
                                    "name": "Thor",
                                    "breed": "Golden Retriever",
                                    "species": "Cachorro",
                                    "age": 5,
                                }
                            ],
                            "thinking": "Executando search_customer_pets...",
                        },
                        {
                            "tool_name": "check_availability",
                            "arguments": {"day": "sábado", "period": "morning"},
                            "result": {"available_slots": ["09:00", "10:30", "11:00"]},
                        },
                    ],
                    "intent_detected": "book_appointment",
                    "confidence_score": 0.95,
                },
                response_only=True,
            ),
        ],
        tags=["AI Intelligence"],
    )
    def post(self, request):
        """Generate scheduling intent from natural language input."""
        serializer = SchedulingIntentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = SchedulingAgentService()
        request_dto = SchedulingIntentRequest(
            user_input=serializer.validated_data["user_input"],
            customer_id=serializer.validated_data.get("customer_id"),
        )

        try:
            result = service.generate_intent(request_dto)

            response_data = {
                "message": result.message,
                "tools_executed": [
                    {
                        "tool_name": t.tool_name,
                        "arguments": t.arguments,
                        "result": t.result,
                        "thinking": t.thinking,
                    }
                    for t in result.tools_executed
                ],
                "intent_detected": result.intent_detected,
                "confidence_score": result.confidence_score,
            }

            response_serializer = SchedulingIntentResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)

            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
