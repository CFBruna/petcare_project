import zoneinfo
from datetime import date

import structlog
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
)
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.core.views import AutoSchemaModelNameMixin
from src.petcare.permissions import IsOwnerOrStaff, IsStaffOrReadOnly

from .models import Appointment, Service, TimeSlot
from .serializers import (
    AppointmentSerializer,
    ServiceSerializer,
    TimeSlotSerializer,
)
from .services import AppointmentService

logger = structlog.get_logger(__name__)


@extend_schema(
    tags=["Schedule - Slots"],
    summary="List available appointment slots",
    parameters=[
        OpenApiParameter(
            name="date",
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description="The desired date in YYYY-MM-DD format.",
            examples=[OpenApiExample("Example", value="2025-12-25")],
        ),
        OpenApiParameter(
            name="service_id",
            type=int,
            location=OpenApiParameter.QUERY,
            required=True,
            description="The ID of the service for the appointment.",
            examples=[OpenApiExample("Example", value=1)],
        ),
    ],
    description="Calculates and returns a list of available time slots for a given service on a specific date.",
)
class AvailableSlotsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            date_str = request.query_params.get("date")
            service_id = request.query_params.get("service_id")

            if not date_str or not service_id:
                logger.warning(
                    "available_slots_missing_params",
                    user=request.user.username,
                )
                return Response(
                    {"error": "Parameters 'date' and 'service_id' are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            appointment_date = date.fromisoformat(date_str)
            service = Service.objects.get(pk=service_id)

            slots = AppointmentService.get_available_slots(appointment_date, service)

            sao_paulo_tz = zoneinfo.ZoneInfo("America/Sao_Paulo")
            time_strings = [
                slot.astimezone(sao_paulo_tz).strftime("%H:%M") for slot in slots
            ]
            return Response(time_strings)

        except Service.DoesNotExist:
            return Response(
                {"error": "Service not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(
    tags=["Schedule - Services"],
    description="Endpoints for managing available services.",
)
class ServiceViewSet(AutoSchemaModelNameMixin, viewsets.ModelViewSet):
    queryset = Service.objects.all().order_by("name")
    serializer_class = ServiceSerializer
    permission_classes = [IsStaffOrReadOnly]
    pagination_class = None


@extend_schema(
    tags=["Schedule - TimeSlots"],
    description="Endpoints for managing the weekly work schedule (for staff/admins).",
)
class TimeSlotViewSet(AutoSchemaModelNameMixin, viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [IsAdminUser]


@extend_schema(
    tags=["Schedule - Appointments"],
    description="Endpoints for users to manage their pets' appointments.",
)
class AppointmentViewSet(AutoSchemaModelNameMixin, viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsOwnerOrStaff]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Appointment.objects.select_related("pet", "service").all()
        return Appointment.objects.filter(pet__owner__user=user).select_related(
            "pet", "service"
        )

    def get_object(self):
        """
        Override get_object to ensure proper 404 when object is not in queryset.
        This prevents users from accessing appointments that don't belong to them.
        """
        from rest_framework.exceptions import NotFound

        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}

        try:
            obj = queryset.get(**filter_kwargs)
        except Appointment.DoesNotExist:
            raise NotFound() from None

        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        appointment = serializer.save()
        logger.info(
            "appointment_created",
            appointment_id=appointment.id,
            pet_id=appointment.pet.id,
            pet_name=appointment.pet.name,
            service_id=appointment.service.id,
            service_name=appointment.service.name,
            scheduled_for=appointment.schedule_time.isoformat(),
            created_by=self.request.user.username,
        )

    def perform_destroy(self, instance):
        logger.warning(
            "appointment_canceled",
            appointment_id=instance.id,
            pet_id=instance.pet.id,
            pet_name=instance.pet.name,
            canceled_by=self.request.user.username,
        )
        instance.delete()
