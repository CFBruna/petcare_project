from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import get_current_customer, register_customer
from .views import CustomerViewSet

router = DefaultRouter()
router.register(r"customers", CustomerViewSet, basename="customer")

urlpatterns = [
    path("register/", register_customer, name="register-customer"),
    path("me/", get_current_customer, name="current-customer"),
    path("", include(router.urls)),
]
