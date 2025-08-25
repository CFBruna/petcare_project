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

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = [IsAuthenticated]
        else:
            from rest_framework.permissions import DjangoModelPermissions

            self.permission_classes = [DjangoModelPermissions]

        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
