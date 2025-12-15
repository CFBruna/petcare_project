from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html

from .forms import BrandAdminForm, CategoryAdminForm, SaleItemFormSet
from .models import (
    ProductLot,
    PromotionRule,
    SaleItem,
)
from .services import InsufficientStockError, SaleService


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
    list_display = [
        "id",
        "display_sold_items",
        "customer",
        "created_at",
        "processed_by",
        "total_value",
    ]
    list_filter = ["created_at", "customer"]
    search_fields = ["id", "customer__user__username"]
    readonly_fields = ["total_value", "processed_by", "created_at"]

    class Media:
        js = ("js/store_admin.js",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("items__lot__product")

    @admin.display(description="Itens Vendidos")
    def display_sold_items(self, obj):
        items = obj.items.all()
        if not items:
            return "—"

        max_items_to_show = 3
        items_to_display = list(items[:max_items_to_show])

        format_placeholders = ["{}x {}" for _ in items_to_display]

        format_args = []
        for item in items_to_display:
            format_args.extend([item.quantity, item.lot.product.name])

        html_format_string = "<br>".join(format_placeholders)

        if len(items) > max_items_to_show:
            html_format_string += "<br>..."

        return format_html(html_format_string, *format_args)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if not self.has_change_permission(request):
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden()
        return super().change_view(request, object_id, form_url, extra_context)

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
            final_sale = SaleService.create_sale(
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
            request._message_sent_for_sale = True
        except InsufficientStockError as e:
            self.message_user(request, str(e), messages.ERROR)
            if not change and sale_instance.pk:
                sale_instance.delete()

    def response_add(self, request, obj, post_url_continue=None):
        if hasattr(request, "_message_sent_for_sale"):
            post_url = reverse(
                f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist"
            )
            return HttpResponseRedirect(post_url)

        return super().response_add(request, obj, post_url_continue)


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
    actions = ["generate_technical_description", "generate_creative_description"]

    @admin.display(description="Preço Final")
    def final_price_display(self, obj):
        return f"R$ {obj.final_price or obj.price}"

    @admin.action(description="🤖 Gerar Descrição Técnica (IA)")
    def generate_technical_description(self, request, queryset):
        """Generate technical product descriptions using AI."""
        from src.apps.ai.services import (
            ProductDescriptionRequest,
            ProductIntelligenceService,
        )

        service = ProductIntelligenceService()
        success_count = 0
        error_count = 0

        for product in queryset:
            try:
                request_dto = ProductDescriptionRequest(
                    product_name=product.name,
                    category=product.category.name if product.category else None,
                    brand=product.brand.name if product.brand else None,
                    price=float(product.price),
                    mode="technical",
                )

                result = service.generate_description(request_dto, user=request.user)

                # Update product description
                product.description = result.description
                product.save()

                success_count += 1

            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Erro ao gerar descrição para {product.name}: {str(e)}",
                    messages.ERROR,
                )

        if success_count > 0:
            self.message_user(
                request,
                f"✅ {success_count} descrição(ões) técnica(s) gerada(s) com sucesso!",
                messages.SUCCESS,
            )

        if error_count > 0:
            self.message_user(
                request,
                f"❌ {error_count} erro(s) ao gerar descrições.",
                messages.WARNING,
            )

    @admin.action(description="✨ Gerar Descrição Criativa (IA)")
    def generate_creative_description(self, request, queryset):
        """Generate creative product descriptions using AI."""
        from src.apps.ai.services import (
            ProductDescriptionRequest,
            ProductIntelligenceService,
        )

        service = ProductIntelligenceService()
        success_count = 0
        error_count = 0

        for product in queryset:
            try:
                request_dto = ProductDescriptionRequest(
                    product_name=product.name,
                    category=product.category.name if product.category else None,
                    brand=product.brand.name if product.brand else None,
                    price=float(product.price),
                    mode="creative",
                )

                result = service.generate_description(request_dto, user=request.user)

                # Update product description
                product.description = result.description
                product.save()

                success_count += 1

            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Erro ao gerar descrição para {product.name}: {str(e)}",
                    messages.ERROR,
                )

        if success_count > 0:
            self.message_user(
                request,
                f"✨ {success_count} descrição(ões) criativa(s) gerada(s) com sucesso!",
                messages.SUCCESS,
            )

        if error_count > 0:
            self.message_user(
                request,
                f"❌ {error_count} erro(s) ao gerar descrições.",
                messages.WARNING,
            )


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

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )
        queryset = queryset.filter(quantity__gt=0)

        if "admin/store/promotion" in request.META.get("HTTP_REFERER", ""):
            queryset = queryset.filter(auto_discount_percentage=0)

        return queryset, use_distinct


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
        original_price_str = f"R$ {obj.product.price:.2f}"
        final_price_str = f"R$ {obj.final_price:.2f}"
        discount = int(obj.auto_discount_percentage)

        html_string = (
            '<span style="text-decoration: line-through;">{}</span><br>'
            '<strong style="color: #4CAF50;">{} (-{}%)</strong>'
        )
        return format_html(
            html_string,
            original_price_str,
            final_price_str,
            discount,
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
