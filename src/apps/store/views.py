from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.core.views import AutoSchemaModelNameMixin
from src.petcare.permissions import IsAdminOrAnonReadOnly

from .models import Brand, Category, Product, ProductLot
from .serializers import BrandSerializer, CategorySerializer, ProductSerializer


@extend_schema(
    tags=["Store - Categories"],
    description="Endpoints to create, read, update, and delete product categories.",
)
class CategoryViewSet(AutoSchemaModelNameMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrAnonReadOnly]

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema(
    tags=["Store - Brands"],
    description="Endpoints for managing product brands.",
)
class BrandViewSet(AutoSchemaModelNameMixin, viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAdminOrAnonReadOnly]

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema(
    tags=["Store - Products"],
    description="Endpoints for managing products and their inventory.",
)
class ProductViewSet(AutoSchemaModelNameMixin, viewsets.ModelViewSet):
    queryset = (
        Product.objects.with_stock()
        .select_related("brand", "category")
        .prefetch_related("lots")
    )
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrAnonReadOnly]


@extend_schema(
    tags=["Store - Lots"],
    parameters=[
        OpenApiParameter(
            name="pk",
            location=OpenApiParameter.PATH,
            description="The ID of the product lot.",
            required=True,
            type=int,
        )
    ],
)
class LotPriceAPIView(APIView):
    permission_classes = [IsAdminUser]
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary="Get the final price of a specific product lot",
        description="Returns the calculated final price for a lot, including any active promotions or automatic discounts.",
    )
    def get(self, request, pk, format=None):
        try:
            lot = ProductLot.objects.select_related("product").get(pk=pk)
            return Response(
                {"price": f"{lot.final_price:.2f}"}, status=status.HTTP_200_OK
            )
        except ProductLot.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
