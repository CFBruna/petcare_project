from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework import status

from .factories import (
    BrandFactory,
    CategoryFactory,
    ProductFactory,
    ProductLotFactory,
    PromotionFactory,
    PromotionRuleFactory,
)


@pytest.mark.django_db
class TestCategoryAPI:
    def setup_method(self):
        self.url = "/api/v1/store/categories/"
        self.category = CategoryFactory()

    def test_unauthenticated_user_cannot_access(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_categories(self, authenticated_client):
        client, user = authenticated_client
        CategoryFactory.create_batch(2)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 3

    def test_retrieve_category(self, authenticated_client):
        client, user = authenticated_client
        response = client.get(f"{self.url}{self.category.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == self.category.name

    def test_create_category(self, authenticated_client):
        client, user = authenticated_client
        data = {"name": "Nova Categoria", "description": "Uma descrição"}
        response = client.post(self.url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["name"] == "Nova Categoria"


@pytest.mark.django_db
class TestBrandAPI:
    def setup_method(self):
        self.url = "/api/v1/store/brands/"
        self.brand = BrandFactory()

    def test_list_brands(self, authenticated_client):
        client, user = authenticated_client
        BrandFactory.create_batch(2)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 3

    def test_retrieve_brand(self, authenticated_client):
        client, user = authenticated_client
        response = client.get(f"{self.url}{self.brand.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == self.brand.name

    def test_create_brand(self, authenticated_client):
        client, user = authenticated_client
        data = {"name": "Nova Marca"}
        response = client.post(self.url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["name"] == "Nova Marca"


@pytest.mark.django_db
class TestProductAPI:
    def setup_method(self):
        self.url = "/api/v1/store/products/"
        self.product = ProductFactory()

    def test_list_products(self, authenticated_client):
        client, user = authenticated_client
        ProductFactory.create_batch(2)
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 3

    def test_retrieve_product(self, authenticated_client):
        client, user = authenticated_client
        response = client.get(f"{self.url}{self.product.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == self.product.name

    def test_create_product(self, authenticated_client):
        client, user = authenticated_client
        category = CategoryFactory()
        brand = BrandFactory()
        data = {
            "name": "Novo Produto",
            "price": "19.99",
            "category": category.id,
            "brand": brand.id,
        }
        response = client.post(self.url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["name"] == "Novo Produto"

    def test_product_serializer_includes_dynamic_prices(self, authenticated_client):
        client, user = authenticated_client
        product = ProductFactory(price=Decimal("200.00"))
        lot = ProductLotFactory(product=product, quantity=10)
        now = timezone.now()
        promotion = PromotionFactory(
            start_date=now - timezone.timedelta(days=1),
            end_date=now + timezone.timedelta(days=1),
        )
        PromotionRuleFactory(promotion=promotion, lot=lot, discount_percentage=50)

        response = client.get(f"{self.url}{product.id}/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["price"] == "200.00"
        assert data["final_price"] == "100.00"


@pytest.mark.django_db
class TestLotPriceAPI:
    def setup_method(self):
        self.lot = ProductLotFactory(product__price=Decimal("50.00"))
        self.url = f"/api/v1/store/lots/{self.lot.id}/price/"

    def test_get_price_for_lot_without_promo(self, authenticated_client):
        client, user = authenticated_client
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["price"] == "50.00"

    def test_get_price_for_lot_with_promo(self, authenticated_client):
        client, user = authenticated_client
        now = timezone.now()
        promotion = PromotionFactory(
            start_date=now - timezone.timedelta(days=1),
            end_date=now + timezone.timedelta(days=1),
        )
        PromotionRuleFactory(promotion=promotion, lot=self.lot, discount_percentage=10)

        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["price"] == "45.00"

    def test_get_price_for_nonexistent_lot_fails(self, authenticated_client):
        client, user = authenticated_client
        invalid_url = "/api/v1/store/lots/9999/price/"
        response = client.get(invalid_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
