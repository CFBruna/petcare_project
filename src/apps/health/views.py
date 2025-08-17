from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import HealthRecord
from .serializers import HealthRecordSerializer


class HealthRecordViewSet(viewsets.ModelViewSet):
    serializer_class = HealthRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        return HealthRecord.objects.filter(pet__owner__user=user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
