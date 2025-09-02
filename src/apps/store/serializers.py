from rest_framework import serializers

from .models import Brand, Category, Product
from .services import ProductService


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "barcode",
            "brand",
            "category",
            "description",
            "price",
            "final_price",
            "total_stock",
            "image",
        ]

    def get_final_price(self, obj: Product) -> str:
        price = ProductService.calculate_product_final_price(obj)
        return f"{price:.2f}"
