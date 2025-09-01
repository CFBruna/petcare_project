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

from src.petcare.permissions import IsOwnerOrStaff, IsStaffOrReadOnly

from .models import Appointment, Service, TimeSlot
from .serializers import (
    AppointmentSerializer,
    ServiceSerializer,
    TimeSlotSerializer,
)


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
        from .services import get_available_slots

        try:
            date_str = request.query_params.get("date")
            service_id = request.query_params.get("service_id")

            if not date_str or not service_id:
                return Response(
                    {"error": "Parameters 'date' and 'service_id' are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            appointment_date = date.fromisoformat(date_str)
            service = Service.objects.get(pk=service_id)

            slots = get_available_slots(appointment_date, service)

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
class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all().order_by("name")
    serializer_class = ServiceSerializer
    permission_classes = [IsStaffOrReadOnly]

    @extend_schema(summary="List all services")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Retrieve a specific service")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Create a new service")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Update a service")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partially update a service")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete a service")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


@extend_schema(
    tags=["Schedule - TimeSlots"],
    description="Endpoints for managing the weekly work schedule (for staff/admins).",
)
class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(summary="List all time slots")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Retrieve a specific time slot")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Create a new time slot")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Update a time slot")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partially update a time slot")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete a time slot")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


@extend_schema(
    tags=["Schedule - Appointments"],
    description="Endpoints for users to manage their pets' appointments.",
)
class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        return Appointment.objects.filter(pet__owner__user=user).select_related(
            "pet", "service"
        )

    def perform_create(self, serializer):
        serializer.save()

    @extend_schema(summary="List the current user's appointments")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Retrieve one of the user's appointments")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new appointment",
        examples=[
            OpenApiExample(
                "Example Request",
                value={
                    "pet": 1,
                    "service": 1,
                    "notes": "My pet is a bit anxious.",
                    "schedule_date": "2025-12-25",
                    "schedule_time": "14:30",
                },
                request_only=True,
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Update an appointment")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partially update an appointment")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Cancel (delete) an appointment")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
