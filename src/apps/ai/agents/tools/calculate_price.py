import structlog
from pydantic import BaseModel, Field

from src.apps.schedule.models import Service

logger = structlog.get_logger(__name__)


class CalculatePriceTool(BaseModel):
    """Calculate the price for a service based on pet size.

    Use this tool when you need to inform the customer about pricing.
    """

    service_name: str = Field(
        description="Service name (e.g., 'banho', 'tosa', 'consulta veterinária')",
    )
    pet_size: str | None = Field(
        default=None,
        description="Pet size category: 'small' (pequeno), 'medium' (médio), or 'large' (grande)",
    )


def calculate_price(
    service_name: str,
    pet_size: str | None = None,
) -> dict:
    """Calculate service price.

    Args:
        service_name: Name of the service
        pet_size: Size category for price adjustment

    Returns:
        Dictionary with price information
    """
    logger.info(
        "calculate_price_started",
        service_name=service_name,
        pet_size=pet_size,
    )

    service = Service.objects.filter(name__icontains=service_name).first()

    if not service:
        return {
            "error": f"Service '{service_name}' not found",
            "price": None,
        }

    base_price = float(service.price)

    size_multipliers = {
        "pequeno": 0.8,
        "small": 0.8,
        "médio": 1.0,
        "medio": 1.0,
        "medium": 1.0,
        "grande": 1.3,
        "large": 1.3,
    }

    multiplier = 1.0
    if pet_size:
        multiplier = size_multipliers.get(pet_size.lower(), 1.0)

    final_price = base_price * multiplier

    logger.info(
        "calculate_price_completed",
        service=service.name,
        base_price=base_price,
        final_price=final_price,
    )

    return {
        "service": service.name,
        "base_price": base_price,
        "final_price": final_price,
        "currency": "BRL",
        "formatted_price": f"R$ {final_price:.2f}",
        "duration_minutes": service.duration_minutes,
        "size_applied": pet_size,
        "notes": service.description if service.description else None,
    }
