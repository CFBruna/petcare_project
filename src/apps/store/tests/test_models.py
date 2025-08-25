import pytest
from django.db.models import ProtectedError

from .factories import (
    BrandFactory,
    CategoryFactory,
    ProductFactory,
    SaleFactory,
    SaleItemFactory,
)


@pytest.mark.django_db
class TestStoreModels:
    def test_category_str(self):
        category = CategoryFactory(name="Brinquedos")
        assert str(category) == "Brinquedos"

    def test_brand_str(self):
        brand = BrandFactory(name="PetSafe")
        assert str(brand) == "PetSafe"

    def test_product_str(self):
        product = ProductFactory(name="Bolinha de Borracha")
        assert str(product) == "Bolinha de Borracha"

    def test_product_has_brand_and_category(self):
        product = ProductFactory()
        assert product.brand is not None
        assert product.category is not None
        assert product.brand.name.startswith("Marca")
        assert product.category.name.startswith("Categoria")

    def test_deleting_category_with_product_fails(self):
        product = ProductFactory()
        category = product.category
        with pytest.raises(ProtectedError):
            category.delete()

    def test_deleting_brand_with_product_fails(self):
        product = ProductFactory()
        brand = product.brand
        with pytest.raises(ProtectedError):
            brand.delete()

    def test_decrease_stock_successfully(self):
        product = ProductFactory(stock=10)
        assert product.decrease_stock(3) is True
        product.refresh_from_db()
        assert product.stock == 7

    def test_decrease_stock_insufficient_stock(self):
        product = ProductFactory(stock=5)
        assert product.decrease_stock(10) is False
        product.refresh_from_db()
        assert product.stock == 5


@pytest.mark.django_db
class TestSaleModels:
    def test_sale_str_representation(self):
        sale = SaleFactory()
        expected_str = f"Venda #{sale.id} - {sale.created_at.strftime('%d/%m/%Y')}"
        assert str(sale) == expected_str

    def test_sale_item_str_representation(self):
        product = ProductFactory(name="Ração Premium")
        sale_item = SaleItemFactory(product=product, quantity=3)
        assert str(sale_item) == "3x Ração Premium"
