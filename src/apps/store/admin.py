from django.contrib import admin, messages

from .forms import BrandAdminForm, CategoryAdminForm, SaleItemFormSet
from .models import (
    Brand,
    Category,
    Product,
    ProductLot,
    Promotion,
    PromotionRule,
    Sale,
    SaleItem,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    form = BrandAdminForm
    list_display = ["name"]
    search_fields = ["name"]


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    formset = SaleItemFormSet
    extra = 1
    autocomplete_fields = ["lot"]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "total_value", "created_at", "processed_by"]
    list_filter = ["created_at", "customer"]
    search_fields = ["id", "customer__user__username"]
    inlines = [SaleItemInline]
    readonly_fields = ["total_value", "processed_by", "created_at"]

    class Media:
        js = ("js/store_admin.js",)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.processed_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        sale = form.instance
        total = 0

        for item in instances:
            if not item.unit_price:
                item.unit_price = item.lot.final_price

            item.lot.quantity -= item.quantity
            item.lot.save()

            item.save()
            total += item.unit_price * item.quantity

        if formset.deleted_objects:
            self.message_user(
                request,
                "Itens removidos não terão estoque restaurado.",
                messages.WARNING,
            )

        sale.total_value = total
        sale.save()
        formset.save_m2m()


class ProductLotInline(admin.TabularInline):
    model = ProductLot
    extra = 1
    fields = ("lot_number", "quantity", "expiration_date", "received_date")
    readonly_fields = ()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "sku",
        "barcode",
        "brand",
        "category",
        "total_stock",
        "price",
        "final_price_display",
    ]
    search_fields = ["name", "sku", "barcode", "brand__name", "category__name"]
    list_filter = ["brand", "category"]
    readonly_fields = ["total_stock", "final_price_display"]
    inlines = [ProductLotInline]

    def final_price_display(self, obj):
        return f"R$ {obj.final_price or obj.price}"

    final_price_display.short_description = "Preço Final"


class PromotionRuleInline(admin.TabularInline):
    model = PromotionRule
    extra = 1
    autocomplete_fields = ("lot",)


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date"]
    inlines = [PromotionRuleInline]


@admin.register(ProductLot)
class ProductLotAdmin(admin.ModelAdmin):
    list_display = ("__str__", "product", "lot_number", "quantity", "expiration_date")
    search_fields = ("product__name", "lot_number", "product__sku", "product__barcode")
