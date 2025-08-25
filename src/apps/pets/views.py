from rest_framework import permissions, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Breed, Pet
from .serializers import BreedSerializer, PetSerializer


class BreedViewSet(viewsets.ModelViewSet):
    queryset = Breed.objects.all()
    serializer_class = BreedSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [permissions.IsAdminUser]

        return super().get_permissions()


class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Pet.objects.filter(owner__user=user)

    def perform_create(self, serializer):
        tutor = self.request.user.customer_profile
        serializer.save(owner=tutor)
