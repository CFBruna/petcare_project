from datetime import date

from rest_framework import permissions, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Appointment, Service, TimeSlot
from .serializers import AppointmentSerializer, ServiceSerializer, TimeSlotSerializer
from .services import get_available_slots


class AvailableSlotsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            date_str = request.query_params.get("date")
            service_id = request.query_params.get("service_id")

            if not date_str or not service_id:
                return Response(
                    {"error": "Os parâmetros 'date' e 'service_id' são obrigatórios."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            appointment_date = date.fromisoformat(date_str)
            service = Service.objects.get(pk=service_id)

            slots = get_available_slots(appointment_date, service)

            formatted_slots = [s.strftime("%H:%M") for s in slots]

            return Response(formatted_slots, status=status.HTTP_200_OK)

        except Service.DoesNotExist:
            return Response(
                {"error": "Serviço não encontrado."}, status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {"error": "Formato de data inválido. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all().order_by("name")
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [permissions.DjangoModelPermissions]
        return super().get_permissions()


class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAdminUser]


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(pet__owner__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()
