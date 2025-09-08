import pytest

from src.apps.accounts.models import Customer
from src.apps.accounts.tests.factories import CustomerFactory
from src.apps.pets.forms import PetAdminForm

from .factories import BreedFactory


@pytest.mark.django_db
class TestPetAdminForm:
    def test_form_is_valid_with_existing_owner(self):
        owner = CustomerFactory()
        breed = BreedFactory()
        form_data = {
            "name": "Fido",
            "owner": owner.id,
            "breed": breed.id,
        }
        form = PetAdminForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_form_is_valid_when_creating_new_customer(self):
        breed = BreedFactory()
        form_data = {
            "name": "Buddy",
            "breed": breed.id,
            "new_customer_username": "new_tutor",
            "new_customer_first_name": "John Doe",
            "new_customer_phone": "987654321",
            "new_customer_cpf": "111.222.333-44",
        }
        form = PetAdminForm(data=form_data)
        assert form.is_valid(), form.errors

    def test_form_save_creates_new_customer_and_pet(self):
        breed = BreedFactory()
        form_data = {
            "name": "Lucy",
            "breed": breed.id,
            "new_customer_username": "lucy_owner",
            "new_customer_first_name": "Jane",
            "new_customer_phone": "123123123",
            "new_customer_cpf": "444.555.666-77",
        }
        form = PetAdminForm(data=form_data)
        assert form.is_valid()

        pet = form.save()
        assert pet.pk is not None
        assert Customer.objects.filter(user__username="lucy_owner").exists()
        assert pet.owner.user.username == "lucy_owner"

    def test_form_invalid_if_no_owner_and_no_new_customer(self):
        breed = BreedFactory()
        form_data = {"name": "Ghost", "breed": breed.id}
        form = PetAdminForm(data=form_data)
        assert not form.is_valid()
        assert "owner" in form.errors

    def test_form_invalid_if_new_username_already_exists(self):
        existing_customer = CustomerFactory()
        breed = BreedFactory()
        form_data = {
            "name": "Garfield",
            "breed": breed.id,
            "new_customer_username": existing_customer.user.username,
        }
        form = PetAdminForm(data=form_data)
        assert not form.is_valid()
        assert "new_customer_username" in form.errors

    def test_form_invalid_if_new_cpf_already_exists(self):
        existing_customer = CustomerFactory()
        breed = BreedFactory()
        form_data = {
            "name": "Nemo",
            "breed": breed.id,
            "new_customer_username": "new_user_for_nemo",
            "new_customer_cpf": existing_customer.cpf,
        }
        form = PetAdminForm(data=form_data)
        assert not form.is_valid()
        assert "new_customer_cpf" in form.errors
