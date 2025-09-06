import structlog
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from src.apps.core.views import AutoSchemaModelNameMixin
from src.petcare.permissions import IsOwnerOrStaff

from .models import HealthRecord
from .serializers import HealthRecordSerializer

logger = structlog.get_logger(__name__)


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
            "health_record_created",
            record_id=health_record.id,
            record_type=health_record.record_type,
            pet_id=health_record.pet.id,
            pet_name=health_record.pet.name,
            created_by=self.request.user.username,
        )
