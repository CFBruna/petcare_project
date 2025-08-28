from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from src.apps.accounts.models import Customer


class Category(models.Model):
    name = models.CharField(
        max_length=100, unique=True, verbose_name="Nome da Categoria"
    )
    description = models.TextField(blank=True, verbose_name="Descrição")

    class Meta:
        ordering = ["name"]
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome da Marca")
    logo = models.ImageField(upload_to="brands/", blank=True, null=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"

    def __str__(self):
        return self.name


class PromotionManager(models.Manager):
    def active(self):
        now = timezone.now()
        return self.get_queryset().filter(
            start_date__lte=now,
            end_date__gte=now,
        )


class Promotion(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nome da Promoção")
    start_date = models.DateTimeField(verbose_name="Data de Início")
    end_date = models.DateTimeField(verbose_name="Data de Fim")

    objects = PromotionManager()

    class Meta:
        verbose_name = "Promoção"
        verbose_name_plural = "Promoções"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=250, verbose_name="Nome do Produto")
    sku = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="SKU (Código Interno)",
        help_text="Código de Referência Interno do Produto.",
    )
    barcode = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Código de Barras (UPC/EAN)",
        help_text="Código de Barras do Fabricante.",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="products",
        blank=True,
        null=True,
        verbose_name="Marca",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        blank=True,
        null=True,
        verbose_name="Categoria",
    )
    description = models.TextField(blank=True, verbose_name="Descrição")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        return self.name

    @property
    def total_stock(self):
        return sum(lot.quantity for lot in self.lots.all())

    @property
    def final_price(self):
        active_promotions = Promotion.objects.active().filter(rules__lot__product=self)
        if not active_promotions.exists():
            return self.price

        earliest_lot_with_promo = (
            self.lots.filter(promotional_rules__promotion__in=active_promotions)
            .order_by("expiration_date")
            .first()
        )

        if earliest_lot_with_promo:
            return earliest_lot_with_promo.final_price

        return self.price


class ProductLot(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="lots",
        verbose_name="Produto",
    )
    lot_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Número do Lote",
        help_text="Código do lote fornecido pelo fabricante.",
    )
    quantity = models.PositiveIntegerField(default=0, verbose_name="Quantidade")
    expiration_date = models.DateField(
        verbose_name="Data de Validade",
        null=True,
        blank=True,
    )
    received_date = models.DateField(
        default=timezone.now, verbose_name="Data de Recebimento"
    )

    class Meta:
        verbose_name = "Lote do Produto"
        verbose_name_plural = "Lotes de Produtos"
        ordering = ["expiration_date"]

    def __str__(self):
        expiration_str = (
            self.expiration_date.strftime("%d/%m/%Y") if self.expiration_date else "N/A"
        )
        return (
            f"Lote de {self.product.name} ({self.quantity} un.) - Val: {expiration_str}"
        )

    @property
    def final_price(self):
        active_rule = self.promotional_rules.filter(
            promotion__in=Promotion.objects.active()
        ).first()

        if active_rule:
            discount_multiplier = active_rule.discount_percentage / Decimal("100")
            discount_amount = self.product.price * discount_multiplier
            return (self.product.price - discount_amount).quantize(Decimal("0.01"))
        return self.product.price


class PromotionRule(models.Model):
    promotion = models.ForeignKey(
        Promotion, on_delete=models.CASCADE, related_name="rules"
    )
    lot = models.ForeignKey(
        ProductLot, on_delete=models.CASCADE, related_name="promotional_rules"
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Desconto (%)",
        help_text="Apenas o número, ex: 10 para 10% de desconto.",
    )
    promotional_stock = models.PositiveIntegerField(
        verbose_name="Quantidade em Promoção",
        help_text="Número de unidades deste lote que estão na promoção.",
    )

    class Meta:
        verbose_name = "Regra da Promoção"
        verbose_name_plural = "Regras da Promoção"

    def clean(self):
        if self.promotional_stock > self.lot.quantity:
            raise ValidationError(
                f"A quantidade em promoção ({self.promotional_stock}) não pode ser maior que a quantidade do lote ({self.lot.quantity})."
            )

    def __str__(self):
        return f"{self.promotion.name} para o lote {self.lot.lot_number or 'N/A'}"


class Sale(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Cliente",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data da Venda")
    total_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Valor Total"
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Processado por",
    )

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Venda #{self.id} - {self.created_at.strftime('%d/%m/%Y')}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    lot = models.ForeignKey(
        ProductLot, on_delete=models.PROTECT, verbose_name="Lote do Produto"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantidade")
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Preço Unitário"
    )

    @property
    def product(self):
        return self.lot.product

    class Meta:
        verbose_name = "Item da Venda"
        verbose_name_plural = "Itens da Venda"

    def __str__(self):
        lot_str = self.lot.lot_number or "N/A"
        return f"{self.quantity}x {self.product.name} (Lote: {lot_str})"
