import logging
from datetime import date

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
)
from rest_framework import permissions, status, viewsets
from rest_framework.permissions import IsAuthenticated
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

logger = logging.getLogger(__name__)


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
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            date_str = request.query_params.get("date")
            service_id = request.query_params.get("service_id")

            if not date_str or not service_id:
                logger.warning(
                    f"AvailableSlotsView was called with missing parameters by user '{request.user.username}'."
                )
                return Response(
                    {"error": "Parameters 'date' and 'service_id' are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            appointment_date = date.fromisoformat(date_str)
            service = Service.objects.get(pk=service_id)

            slots = AppointmentService.get_available_slots(appointment_date, service)

            formatted_slots = [s.strftime("%H:%M") for s in slots]

            return Response(formatted_slots, status=status.HTTP_200_OK)

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


@extend_schema(
    tags=["Schedule - TimeSlots"],
    description="Endpoints for managing the weekly work schedule (for staff/admins).",
)
class TimeSlotViewSet(AutoSchemaModelNameMixin, viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAdminUser]


@extend_schema(
    tags=["Schedule - Appointments"],
    description="Endpoints for users to manage their pets' appointments.",
)
class AppointmentViewSet(AutoSchemaModelNameMixin, viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        return Appointment.objects.filter(pet__owner__user=user).select_related(
            "pet", "service"
        )

    def perform_create(self, serializer):
        appointment = serializer.save()
        logger.info(
            f"Appointment #{appointment.id} created for pet '{appointment.pet.name}' "
            f"by user '{self.request.user.username}' for {appointment.schedule_time}."
        )

    def perform_destroy(self, instance):
        logger.warning(
            f"Appointment #{instance.id} for pet '{instance.pet.name}' was CANCELED "
            f"by user '{self.request.user.username}'."
        )
        instance.delete()
