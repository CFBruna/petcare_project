from django.contrib import admin

from .models import Brand, Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "brand", "category", "stock", "price"]
    search_fields = ["name", "brand__name", "category__name"]
    list_filter = ["brand", "category"]
