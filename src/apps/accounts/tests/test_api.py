import pytest
from rest_framework import status

from .factories import CustomerFactory

URL = "/api/v1/accounts/customers/"


@pytest.mark.django_db
class TestCustomerAPI:
    def test_list_customers_unauthenticated(self, api_client):
        CustomerFactory.create_batch(3)
        response = api_client.get(URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_customers_authenticated(self, authenticated_client):
        client, user = authenticated_client
        CustomerFactory.create_batch(3)
        response = client.get(URL)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["count"] == 3
        assert len(data["results"]) == 3

    def test_retrieve_customer_detail(self, authenticated_client):
        client, user = authenticated_client
        customer = CustomerFactory()
        response = client.get(f"{URL}{customer.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user"]["username"] == customer.user.username
        assert response.json()["cpf"] == customer.cpf
