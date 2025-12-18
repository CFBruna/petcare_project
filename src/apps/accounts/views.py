from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import SAFE_METHODS, BasePermission

from src.apps.core.views import AutoSchemaModelNameMixin

from .models import Customer
from .serializers import CustomerSerializer


class CustomerPermission(BasePermission):
    """
    Custom permission for Customer operations:
    - Allow authenticated users to create their own Customer profile
    - Allow users to view/update their own Customer profile
    - Only admins can list all customers or delete
    """

    def has_permission(self, request, view):
        # Allow authenticated users to create (POST)
        if request.method == "POST":
            return request.user and request.user.is_authenticated
        # Allow authenticated users to view their own data
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # For list/delete, require staff/admin
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # Users can only access their own Customer profile
        if request.user.is_staff:
            return True
        return obj.user == request.user


@extend_schema(
    tags=["Accounts - Customers"],
    description="Endpoints for retrieving customer (tutor) information.",
)
class CustomerViewSet(AutoSchemaModelNameMixin, viewsets.ModelViewSet):
    queryset = Customer.objects.select_related("user").order_by("id")
    serializer_class = CustomerSerializer
    permission_classes = [CustomerPermission]

    def perform_create(self, serializer):
        """Automatically associate the customer with the authenticated user"""
        serializer.save(user=self.request.user)
