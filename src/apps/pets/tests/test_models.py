import pytest

from .factories import BreedFactory, PetFactory


@pytest.mark.django_db
class TestBreedModel:
    def test_breed_str_representation(self):
        breed = BreedFactory(name="Golden Retriever")
        assert str(breed) == "Golden Retriever"

    def test_breed_str_with_different_species(self):
        breed = BreedFactory(name="Siamese", species="CAT")
        assert str(breed) == "Siamese"


@pytest.mark.django_db
class TestPetModel:
    def test_pet_str_representation(self):
        pet = PetFactory(name="Buddy", breed__name="Golden Retriever")
        assert str(pet) == "Buddy - Golden Retriever"

    def test_pet_str_with_different_breed(self):
        pet = PetFactory(name="Whiskers", breed__name="Siamese")
        assert str(pet) == "Whiskers - Siamese"
