import pytest
from django.db.models import ProtectedError

from .factories import BrandFactory, CategoryFactory, ProductFactory


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
