import pytest
from django.test import Client
from django.urls import reverse
from rest_framework import status

from src.apps.store.tests.factories import SaleFactory, SaleItemFactory


@pytest.mark.django_db
class TestSaleAdmin:
    def test_display_sold_items_in_changelist(self, admin_client):
        sale = SaleFactory()
        item1 = SaleItemFactory(sale=sale, quantity=2)
        item2 = SaleItemFactory(sale=sale, quantity=1)

        changelist_url = reverse("petcare_admin:store_sale_changelist")
        response = admin_client.get(changelist_url)

        assert response.status_code == status.HTTP_200_OK
        expected_html_item1 = f"{item1.quantity}x {item1.product.name}"
        expected_html_item2 = f"{item2.quantity}x {item2.product.name}"
        self.assertContains(response, expected_html_item1)
        self.assertContains(response, expected_html_item2)

    def test_change_view_is_forbidden_for_staff_user(self, client, staff_user):
        client.force_login(staff_user)

        sale = SaleFactory()
        change_url = reverse("petcare_admin:store_sale_change", args=[sale.id])

        response = client.get(change_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_change_view_is_forbidden_for_superuser_as_well(self, admin_client):
        sale = SaleFactory()
        change_url = reverse("petcare_admin:store_sale_change", args=[sale.id])

        response = admin_client.get(change_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.fixture
    def client(self):
        return Client()

    def assertContains(self, response, text, status_code=200):
        assert response.status_code == status_code
        assert text in str(response.content)
