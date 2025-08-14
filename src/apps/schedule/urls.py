from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AppointmentViewSet,
    AvailableSlotsView,
    ServiceViewSet,
    TimeSlotViewSet,
)

router = DefaultRouter()
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"time-slots", TimeSlotViewSet, basename="timeslot")
router.register(r"appointments", AppointmentViewSet, basename="appointment")

urlpatterns = [
    path("", include(router.urls)),
    path("available-slots/", AvailableSlotsView.as_view(), name="available-slots"),
]
