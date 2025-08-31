from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import HealthRecord
from .serializers import HealthRecordSerializer


@extend_schema(
    tags=["Health - Records"],
    description="Endpoints for users to manage their pets' health records.",
)
class HealthRecordViewSet(viewsets.ModelViewSet):
    serializer_class = HealthRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return HealthRecord.objects.filter(pet__owner__user=user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(summary="List health records for the user's pets")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Retrieve a specific health record")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new health record",
        examples=[
            OpenApiExample(
                "Example vaccine record",
                value={
                    "pet": 1,
                    "record_type": "VACCINE",
                    "description": "Rabies vaccine, Lot #XYZ123",
                    "record_date": "2025-08-30",
                    "next_due_date": "2026-08-30",
                },
                request_only=True,
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Update a health record")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partially update a health record")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete a health record")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
