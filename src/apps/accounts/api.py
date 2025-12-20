from django.contrib.auth.models import User
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Customer
from .serializers import CustomerSerializer, RegistrationResponseSerializer


@extend_schema(
    tags=["Accounts - Registration"],
    description="Complete user registration with customer profile in a single atomic transaction",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "email": {"type": "string"},
                "password": {"type": "string"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "cpf": {"type": "string"},
                "phone": {"type": "string"},
                "address": {"type": "string"},
            },
            "required": ["username", "email", "password", "cpf", "phone", "address"],
        }
    },
    responses={
        201: RegistrationResponseSerializer,
        400: {"description": "Validation error"},
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register_customer(request):
    """
    Atomic registration endpoint that creates User and Customer in a single transaction.
    If any step fails, everything is rolled back.
    """
    data = request.data

    required_fields = ["username", "email", "password", "cpf", "phone", "address"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return Response(
            {"error": f"Missing required fields: {', '.join(missing_fields)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        with transaction.atomic():
            if User.objects.filter(username=data["username"]).exists():
                return Response(
                    {"username": ["Um usuário com este nome de usuário já existe."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if User.objects.filter(email=data["email"]).exists():
                return Response(
                    {"email": ["Um usuário com este email já existe."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if Customer.objects.filter(cpf=data["cpf"]).exists():
                return Response(
                    {"cpf": ["Um cliente com este CPF já existe."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=data["password"],
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
            )

            customer = Customer.objects.create(
                user=user,
                cpf=data["cpf"],
                phone=data["phone"],
                address=data["address"],
            )

            token, _ = Token.objects.get_or_create(user=user)

            customer_serializer = CustomerSerializer(customer)

            return Response(
                {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    "customer": customer_serializer.data,
                    "token": token.key,
                },
                status=status.HTTP_201_CREATED,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=["Accounts - Current User"],
    description="Get the authenticated user's customer profile",
    responses={
        200: CustomerSerializer,
        404: {"description": "Customer profile not found"},
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_customer(request):
    """
    Get the customer profile for the authenticated user.
    """
    if not request.user.is_authenticated:
        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        customer = Customer.objects.select_related("user").get(user=request.user)
        serializer = CustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Customer.DoesNotExist:
        return Response(
            {"error": "Customer profile not found for this user"},
            status=status.HTTP_404_NOT_FOUND,
        )
