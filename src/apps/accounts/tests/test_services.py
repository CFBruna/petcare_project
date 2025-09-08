import pytest

from src.apps.accounts.models import Customer
from src.apps.accounts.services import CustomerService


@pytest.mark.django_db
class TestCustomerService:
    def test_create_customer_successfully(self):
        customer = CustomerService.create_customer(
            username="newuser",
            first_name="New",
            phone="123456789",
            cpf="123.456.789-00",
        )

        assert Customer.objects.count() == 1
        assert customer.user.username == "newuser"
        assert customer.cpf == "123.456.789-00"
