from datetime import datetime

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Appointment, Service, TimeSlot
from .serializers import AppointmentSerializer, ServiceSerializer, TimeSlotSerializer
from .services import get_available_slots


class AvailableSlotsView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            date_str = request.query_params.get("date")
            service_id = request.query_params.get("service_id")

            if not date_str or not service_id:
                return Response(
                    {"error": "Os parâmetros 'date' e 'service_id' são obrigatórios."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            service = Service.objects.get(pk=service_id)

            slots = get_available_slots(date, service)

            formatted_slots = [s.strftime("%H:%M") for s in slots]

            return Response(formatted_slots, status=status.HTTP_200_OK)

        except Service.DoesNotExist:
            return Response(
                {"error": "Serviço não encontrado."}, status=status.HTTP_404_NOT_FOUND
            )
        except (ValueError, TypeError):
            return Response(
                {"error": "Formato de data inválido. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
