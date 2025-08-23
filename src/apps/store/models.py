from django.conf import settings
from django.db import models

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


class Product(models.Model):
    name = models.CharField(max_length=250, verbose_name="Nome do Produto")
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
    stock = models.PositiveIntegerField(default=0, verbose_name="Estoque")
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        return self.name

    def decrease_stock(self, quantity):
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False


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
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, verbose_name="Produto"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantidade")
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Preço Unitário"
    )

    class Meta:
        verbose_name = "Item da Venda"
        verbose_name_plural = "Itens da Venda"

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
