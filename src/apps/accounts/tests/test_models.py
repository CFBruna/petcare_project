import pytest
from django.contrib.auth.models import User

from src.apps.accounts.tests.factories import CustomerFactory, UserFactory


@pytest.mark.django_db
def test_user_creation():
    User.objects.create_user(username="testuser", password="password123")
    assert User.objects.count() == 1


@pytest.mark.django_db
class TestCustomerModel:
    def test_customer_str_representation(self):
        user = UserFactory(first_name="João", last_name="Silva")
        customer = CustomerFactory(user=user)
        assert str(customer) == f"{user.get_full_name()} - {customer.cpf}"

    def test_customer_full_name_property(self):
        user = UserFactory(first_name="Maria", last_name="Oliveira")
        customer = CustomerFactory(user=user)
        assert customer.full_name == "Maria Oliveira"

    def test_customer_str_representation_no_full_name(self):
        user = UserFactory(first_name="", last_name="")
        customer = CustomerFactory(user=user)
        assert str(customer) == f"{user.username} - {customer.cpf}"
