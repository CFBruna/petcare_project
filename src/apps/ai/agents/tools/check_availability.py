import re
from datetime import date, datetime, timedelta

import structlog
from django.utils import timezone
from pydantic import BaseModel, Field

from src.apps.schedule.models import Service
from src.apps.schedule.services import AppointmentService

logger = structlog.get_logger(__name__)


class CheckAvailabilityTool(BaseModel):
    """Check available appointment slots for a specific day and service.

    Use this tool to find when appointments are available.
    """

    day: str = Field(
        description="Day specification: weekday name (e.g., 'saturday', 'sábado') or ISO date (e.g., '2024-12-20')",
    )
    period: str | None = Field(
        default=None,
        description="Time period: 'morning' (manhã), 'afternoon' (tarde), or 'evening' (noite)",
    )
    service_name: str | None = Field(
        default=None,
        description="Service name (e.g., 'banho', 'tosa', 'consulta')",
    )


def check_availability(
    day: str,
    period: str | None = None,
    service_name: str | None = None,
) -> dict:
    """Check available slots for appointments.

    Args:
        day: Day of week or ISO date
        period: morning, afternoon, or evening
        service_name: Service name to check

    Returns:
        Dictionary with available slots and metadata
    """
    logger.info(
        "check_availability_started",
        day=day,
        period=period,
        service_name=service_name,
    )

    schedule_date = _parse_day_to_date(day)
    if not schedule_date:
        return {
            "error": f"Não consegui interpretar o dia: {day}",
            "available_slots": [],
        }

    service = None
    if service_name:
        service = Service.objects.filter(name__icontains=service_name).first()

    if not service:
        service = Service.objects.first()
        if not service:
            return {
                "error": "Nenhum serviço encontrado no sistema",
                "available_slots": [],
            }

    slots = AppointmentService.get_available_slots(schedule_date, service)

    if period:
        slots = _filter_slots_by_period(slots, period)

    formatted_slots = [
        {
            "datetime": slot.isoformat(),
            "time": slot.strftime("%H:%M"),
            "date": slot.strftime("%d/%m/%Y"),
            "day_of_week": _get_day_name(slot.weekday()),
        }
        for slot in slots[:10]
    ]

    logger.info(
        "check_availability_completed",
        date=schedule_date,
        slots_found=len(formatted_slots),
    )

    return {
        "date": schedule_date.strftime("%d/%m/%Y"),
        "day_of_week": _get_day_name(schedule_date.weekday()),
        "service": service.name,
        "service_duration_minutes": service.duration_minutes,
        "available_slots": formatted_slots,
        "total_slots": len(formatted_slots),
    }


def _parse_day_to_date(day: str) -> date | None:
    """Parse day string into date object."""
    day_lower = day.lower().strip()

    if re.match(r"\d{4}-\d{2}-\d{2}", day):
        try:
            return datetime.fromisoformat(day).date()
        except ValueError:
            pass

    today = timezone.now().date()
    weekdays_pt = {
        "segunda": 0,
        "segunda-feira": 0,
        "terça": 1,
        "terca": 1,
        "terça-feira": 1,
        "terca-feira": 1,
        "quarta": 2,
        "quarta-feira": 2,
        "quinta": 3,
        "quinta-feira": 3,
        "sexta": 4,
        "sexta-feira": 4,
        "sábado": 5,
        "sabado": 5,
        "domingo": 6,
    }
    weekdays_en = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    target_weekday = weekdays_pt.get(day_lower) or weekdays_en.get(day_lower)
    if target_weekday is not None:
        days_ahead = target_weekday - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    if day_lower in ["hoje", "today"]:
        return today
    if day_lower in ["amanhã", "amanha", "tomorrow"]:
        return today + timedelta(days=1)

    return None


def _filter_slots_by_period(slots: list[datetime], period: str) -> list[datetime]:
    """Filter slots by time period."""
    period_lower = period.lower()

    # Morning: 6-12
    if period_lower in ["morning", "manhã", "manha"]:
        return [s for s in slots if 6 <= s.hour < 12]

    # Afternoon: 12-18
    if period_lower in ["afternoon", "tarde"]:
        return [s for s in slots if 12 <= s.hour < 18]

    # Evening: 18-23
    if period_lower in ["evening", "noite"]:
        return [s for s in slots if 18 <= s.hour < 23]

    return slots


def _get_day_name(weekday: int) -> str:
    """Get Portuguese day name from weekday number."""
    names = [
        "Segunda-feira",
        "Terça-feira",
        "Quarta-feira",
        "Quinta-feira",
        "Sexta-feira",
        "Sábado",
        "Domingo",
    ]
    return names[weekday]
