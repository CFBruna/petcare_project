from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from src.petcare.permissions import IsStaffOrReadOnly

from .models import Breed, Pet
from .serializers import BreedSerializer, PetSerializer


class BreedViewSet(viewsets.ModelViewSet):
    queryset = Breed.objects.all()
    serializer_class = BreedSerializer
    permission_classes = [IsStaffOrReadOnly]


class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all().order_by("name")
    serializer_class = PetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Pet.objects.filter(owner__user=user).order_by("name")

    def perform_create(self, serializer):
        tutor = self.request.user.customer_profile
        serializer.save(owner=tutor)
