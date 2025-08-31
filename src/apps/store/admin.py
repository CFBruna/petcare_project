from django.contrib import admin, messages
from django.utils.html import format_html

from .forms import BrandAdminForm, CategoryAdminForm, SaleItemFormSet
from .models import (
    ProductLot,
    PromotionRule,
    SaleItem,
)
from .services import InsufficientStockError, create_sale


class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ["name", "description"]
    search_fields = ["name"]


class BrandAdmin(admin.ModelAdmin):
    form = BrandAdminForm
    list_display = ["name"]
    search_fields = ["name"]


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    formset = SaleItemFormSet
    extra = 1
    autocomplete_fields = ["lot"]
    fields = ["lot", "quantity", "unit_price"]


class SaleAdmin(admin.ModelAdmin):
    inlines = [SaleItemInline]
    list_display = ["id", "customer", "total_value", "created_at", "processed_by"]
    list_filter = ["created_at", "customer"]
    search_fields = ["id", "customer__user__username"]
    readonly_fields = ["total_value", "processed_by", "created_at"]

    class Media:
        js = ("js/store_admin.js",)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        if not change:
            obj.processed_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        if not formset.is_valid():
            return super().save_formset(request, form, formset, change)

        items_data = []
        for f in formset.cleaned_data:
            if f and not f.get("DELETE") and "lot" in f:
                items_data.append(
                    {
                        "lot": f["lot"],
                        "quantity": f["quantity"],
                        "unit_price": f["lot"].final_price,
                    }
                )

        sale_instance = form.instance
        if not items_data:
            if not change and sale_instance.pk:
                self.message_user(
                    request,
                    "Venda cancelada pois não continha itens.",
                    messages.WARNING,
                )
                sale_instance.delete()
            return

        try:
            final_sale = create_sale(
                user=request.user,
                customer=sale_instance.customer,
                items_data=items_data,
                sale_instance=sale_instance,
            )

            formset.new_objects = final_sale.items.all()
            formset.changed_objects = []
            formset.deleted_objects = []

            for f in formset.forms:
                f.instance.sale = final_sale

            self.message_user(request, "Venda criada com sucesso!", messages.SUCCESS)
        except InsufficientStockError as e:
            self.message_user(request, str(e), messages.ERROR)
            if not change and sale_instance.pk:
                sale_instance.delete()


class ProductLotInline(admin.TabularInline):
    model = ProductLot
    extra = 1
    fields = ("lot_number", "quantity", "expiration_date", "received_date")


class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductLotInline]
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
    readonly_fields = ["total_stock"]

    @admin.display(description="Preço Final")
    def final_price_display(self, obj):
        return f"R$ {obj.final_price or obj.price}"


class PromotionRuleInline(admin.TabularInline):
    model = PromotionRule
    extra = 1
    autocomplete_fields = ("lot",)


class PromotionAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date"]
    inlines = [PromotionRuleInline]


class ProductLotAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "product",
        "lot_number",
        "quantity",
        "expiration_date",
        "auto_discount_percentage",
    )
    search_fields = ("product__name", "lot_number", "product__sku", "product__barcode")
    readonly_fields = ("auto_discount_percentage",)


class AutoPromotionAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "lot_number",
        "expiration_date",
        "quantity",
        "price_with_discount",
    )
    list_display_links = None
    search_fields = ("product__name", "lot_number")
    ordering = ("expiration_date",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(auto_discount_percentage__gt=0, quantity__gt=0)
        )

    @admin.display(description="Preço Final")
    def price_with_discount(self, obj):
        original_price = obj.product.price
        final_price = obj.final_price
        discount = int(obj.auto_discount_percentage)
        html_string = (
            f'<span style="text-decoration: line-through;">R$ {original_price:.2f}</span><br>'
            f'<strong style="color: #4CAF50;">R$ {final_price:.2f} (-{discount}%)</strong>'
        )
        return format_html(html_string)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
