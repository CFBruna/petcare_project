import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from src.apps.accounts.models import Customer

User = get_user_model()


@pytest.mark.django_db
class TestCustomerRegistrationAPI:
    def setup_method(self):
        self.client = APIClient()
        self.url = "/api/v1/accounts/register/"
        self.valid_data = {
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "testpass123",
            "cpf": "12345678901",
            "phone": "11987654321",
            "address": "Test Street, 123",
        }

    def test_successful_registration(self):
        response = self.client.post(self.url, data=self.valid_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert "token" in response.data
        assert "customer" in response.data
        assert User.objects.filter(username="newuser").exists()
        assert Customer.objects.filter(cpf="12345678901").exists()

    def test_registration_missing_fields(self):
        incomplete_data = {"username": "test", "email": "test@test.com"}
        response = self.client.post(self.url, data=incomplete_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data
        assert "Missing required fields" in response.data["error"]

    def test_registration_duplicate_username(self):
        User.objects.create_user(username="newuser", email="other@test.com")
        response = self.client.post(self.url, data=self.valid_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data

    def test_registration_duplicate_email(self):
        User.objects.create_user(username="other", email="newuser@test.com")
        response = self.client.post(self.url, data=self.valid_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_registration_duplicate_cpf(self):
        user = User.objects.create_user(username="other", email="other@test.com")
        Customer.objects.create(
            user=user, cpf="12345678901", phone="11999999999", address="Other"
        )
        response = self.client.post(self.url, data=self.valid_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cpf" in response.data


@pytest.mark.django_db
class TestGetCurrentCustomerAPI:
    def setup_method(self):
        self.client = APIClient()
        self.url = "/api/v1/accounts/me/"

    def test_get_current_customer_authenticated(self):
        user = User.objects.create_user(username="testuser", email="test@test.com")
        Customer.objects.create(
            user=user, cpf="11122233344", phone="11987654321", address="Test"
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["cpf"] == "11122233344"
        assert response.data["user"]["username"] == "testuser"

    def test_get_current_customer_no_profile(self):
        user = User.objects.create_user(username="noProfile", email="no@test.com")
        self.client.force_authenticate(user=user)

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.data["error"].lower()

    def test_get_current_customer_unauthenticated(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
