import logging

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from src.apps.core.views import AutoSchemaModelNameMixin
from src.petcare.permissions import IsOwnerOrStaff

from .models import HealthRecord
from .serializers import HealthRecordSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Health - Records"],
    description="Endpoints for users to manage their pets' health records.",
)
class HealthRecordViewSet(AutoSchemaModelNameMixin, viewsets.ModelViewSet):
    serializer_class = HealthRecordSerializer
    permission_classes = [IsOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        return HealthRecord.objects.filter(pet__owner__user=user).select_related(
            "pet", "created_by"
        )

    def perform_create(self, serializer):
        health_record = serializer.save(created_by=self.request.user)
        logger.info(
            f"HealthRecord #{health_record.id} (Type: {health_record.record_type}) created for pet "
            f"'{health_record.pet.name}' by user '{self.request.user.username}'."
        )
