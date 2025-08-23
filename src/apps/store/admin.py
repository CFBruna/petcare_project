from django.contrib import admin, messages

from .models import Brand, Category, Product, Sale, SaleItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    autocomplete_fields = ["product"]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "total_value", "created_at", "processed_by"]
    list_filter = ["created_at", "customer"]
    search_fields = ["id", "customer__user__username"]
    inlines = [SaleItemInline]
    readonly_fields = ["total_value", "processed_by", "created_at"]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.processed_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        sale = form.instance
        total = 0

        for item in instances:
            item.unit_price = item.product.price
            item.save()
            total += item.unit_price * item.quantity
            if not item.product.decrease_stock(item.quantity):
                self.message_user(
                    request,
                    f"Estoque insuficiente para o produto {item.product.name}.",
                    messages.ERROR,
                )

        if formset.deleted_objects:
            self.message_user(
                request,
                messages.WARNING,
            )

        sale.total_value = total
        sale.save()
        formset.save_m2m()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "brand", "category", "stock", "price"]
    search_fields = ["name", "brand__name", "category__name"]
    list_filter = ["brand", "category"]
    search_fields = ["name"]
