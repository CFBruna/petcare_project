import pytest

from src.apps.pets.forms import BreedAdminForm, PetAdminForm

from .factories import BreedFactory, CustomerFactory, PetFactory


@pytest.mark.django_db
class TestBreedModel:
    def test_breed_str_representation(self):
        breed = BreedFactory(name="Golden Retriever")
        assert str(breed) == "Golden Retriever"

    def test_form_prevents_duplicate_breed_name(self):
        BreedFactory(name="Spitz Alemão")

        form_data = {"name": "spitz alemão", "species": "DOG"}
        form = BreedAdminForm(data=form_data)

        assert not form.is_valid()
        assert "name" in form.errors
        assert "Uma raça com este nome já existe." in form.errors["name"][0]


@pytest.mark.django_db
class TestPetModel:
    def test_pet_str_representation(self):
        pet = PetFactory(name="Buddy", breed__name="Golden Retriever")
        owner_name = pet.owner.full_name or pet.owner.user.username

        expected_str = f"Buddy - Tutor: {owner_name}"
        assert str(pet) == expected_str

    def test_pet_str_with_different_breed(self):
        pet = PetFactory(name="Whiskers", breed__name="Siamese")
        owner_name = pet.owner.full_name or pet.owner.user.username

        expected_str = f"Whiskers - Tutor: {owner_name}"
        assert str(pet) == expected_str

    def test_form_prevents_duplicate_pet_for_same_owner(self):
        owner = CustomerFactory()
        breed = BreedFactory()
        PetFactory(name="Rex", owner=owner, breed=breed)

        form_data = {
            "name": "rex",
            "owner": owner.id,
            "breed": breed.id,
        }
        form = PetAdminForm(data=form_data)

        assert not form.is_valid()
        assert "já possui um pet com o nome" in str(form.errors)
