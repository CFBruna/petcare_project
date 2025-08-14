from rest_framework import viewsets

from .models import HealthRecord
from .serializers import HealthRecordSerializer


class HealthRecordViewSet(viewsets.ModelViewSet):
    queryset = HealthRecord.objects.all()
    serializer_class = HealthRecordSerializer
