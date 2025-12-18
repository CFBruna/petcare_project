from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from src.apps.accounts.models import Customer
from src.apps.core.views import AutoSchemaModelNameMixin
from src.petcare.permissions import IsOwnerOrStaff, IsStaffOrReadOnly

from .models import Breed, Pet
from .serializers import BreedSerializer, PetSerializer


@extend_schema(
    tags=["Pets - Breeds"],
    description="Endpoints for managing pet breeds (for staff/admins).",
)
class BreedViewSet(AutoSchemaModelNameMixin, viewsets.ModelViewSet):
    queryset = Breed.objects.all()
    serializer_class = BreedSerializer
    permission_classes = [IsStaffOrReadOnly]
    pagination_class = None


@extend_schema(
    tags=["Pets - Pets"],
    description="Endpoints for users to manage their own pets.",
)
class PetViewSet(AutoSchemaModelNameMixin, viewsets.ModelViewSet):
    serializer_class = PetSerializer
    permission_classes = [IsOwnerOrStaff]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return (
            Pet.objects.filter(owner__user=user)
            .select_related("breed", "owner__user")
            .order_by("name")
        )

    def perform_create(self, serializer):
        try:
            customer = Customer.objects.get(user=self.request.user)
            serializer.save(owner=customer)
        except Customer.DoesNotExist:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("No customer profile found for this user") from None
