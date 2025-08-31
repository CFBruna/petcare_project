from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from .models import Customer
from .serializers import CustomerSerializer


@extend_schema(
    tags=["Accounts - Customers"],
    description="Endpoints for retrieving customer (tutor) information.",
)
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("id")
    serializer_class = CustomerSerializer

    @extend_schema(summary="List all customers (staff only)")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Retrieve a specific customer (staff only)")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Create a customer (not used, tied to user registration)")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Update a customer (staff only)")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partially update a customer (staff only)")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete a customer (staff only)")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
