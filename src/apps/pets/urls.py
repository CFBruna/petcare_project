from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BreedViewSet, PetViewSet

router = DefaultRouter()
router.register(r"breeds", BreedViewSet, basename="breed")
router.register(r"pets", PetViewSet, basename="pet")

urlpatterns = [
    path("", include(router.urls)),
]
