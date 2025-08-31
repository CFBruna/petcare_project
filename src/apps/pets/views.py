from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from src.petcare.permissions import IsStaffOrReadOnly

from .models import Breed, Pet
from .serializers import BreedSerializer, PetSerializer


@extend_schema(
    tags=["Pets - Breeds"],
    description="Endpoints for managing pet breeds (for staff/admins).",
)
class BreedViewSet(viewsets.ModelViewSet):
    queryset = Breed.objects.all()
    serializer_class = BreedSerializer
    permission_classes = [IsStaffOrReadOnly]

    @extend_schema(summary="List all breeds")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Retrieve a specific breed")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Create a new breed")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Update a breed")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partially update a breed")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete a breed")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


@extend_schema(
    tags=["Pets - Pets"],
    description="Endpoints for users to manage their own pets.",
)
class PetViewSet(viewsets.ModelViewSet):
    serializer_class = PetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Pet.objects.filter(owner__user=user)
            .select_related("breed", "owner__user")
            .order_by("name")
        )

    def perform_create(self, serializer):
        tutor = self.request.user.customer_profile
        serializer.save(owner=tutor)

    @extend_schema(summary="List the current user's pets")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Retrieve one of the user's pets")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Register a new pet for the current user")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Update a pet's information")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partially update a pet's information")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete one of the user's pets")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
