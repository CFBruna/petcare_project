from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from src.apps.core.views import AutoSchemaModelNameMixin

from .models import Customer
from .serializers import CustomerSerializer


@extend_schema(
    tags=["Accounts - Customers"],
    description="Endpoints for retrieving customer (tutor) information.",
)
class CustomerViewSet(AutoSchemaModelNameMixin, viewsets.ModelViewSet):
    queryset = Customer.objects.select_related("user").order_by("id")
    serializer_class = CustomerSerializer
