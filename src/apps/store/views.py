from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from src.petcare.permissions import IsStaffOrReadOnly

from .models import Brand, Category, Product, ProductLot
from .serializers import BrandSerializer, CategorySerializer, ProductSerializer


@extend_schema(
    tags=["Store - Categories"],
    description="Endpoints to create, read, update, and delete product categories.",
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]

    @extend_schema(
        summary="List all categories",
        description="Returns a paginated list of all product categories registered in the system.",
    )
    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new category",
        description="Creates a new product category. Requires staff permissions.",
        examples=[
            OpenApiExample(
                "Example Request",
                value={"name": "Toys", "description": "All kinds of pet toys."},
                request_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


@extend_schema(tags=["Store - Brands"])
class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsStaffOrReadOnly]

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema(tags=["Store - Products"])
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("brand", "category").prefetch_related(
        "lots"
    )
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]


@extend_schema(tags=["Store - Lots"])
class LotPriceAPIView(APIView):
    permission_classes = [IsAdminUser]
    renderer_classes = [JSONRenderer]

    def get(self, request, pk, format=None):
        try:
            lot = ProductLot.objects.select_related("product").get(pk=pk)
            return Response(
                {"price": f"{lot.final_price:.2f}"}, status=status.HTTP_200_OK
            )
        except ProductLot.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
