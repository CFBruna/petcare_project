import pytest
from rest_framework import status

from src.apps.accounts.models import Customer
from src.apps.pets.models import Breed, Pet

from .factories import BreedFactory, PetFactory


@pytest.mark.django_db
class TestBreedAPI:
    def test_list_breeds_unauthorized(self, api_client):
        BreedFactory.create_batch(3)
        url = "/api/v1/pets/breeds/"

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_breed_unauthorized(self, api_client):
        url = "/api/v1/pets/breeds/"
        data = {"name": "Nova Raça", "species": "DOG"}

        response = api_client.post(url, data=data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_and_create_breed_authorized(self, authenticated_client):
        client, user = authenticated_client
        url = "/api/v1/pets/breeds/"
        response_get = client.get(url)
        assert response_get.status_code == status.HTTP_200_OK

        data = {"name": "Nova Raça Autorizada", "species": "CAT"}
        response_post = client.post(url, data=data)
        assert response_post.status_code == status.HTTP_201_CREATED
        assert Breed.objects.filter(name="Nova Raça Autorizada").exists()


@pytest.mark.django_db
class TestPetAPI:
    def test_list_pets_unauthorized(self, api_client):
        PetFactory.create_batch(2)
        url = "/api/v1/pets/pets/"

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_pet_authorized(self, authenticated_client):
        client, user = authenticated_client
        # Ensure the authenticated user has a customer profile
        customer, _ = Customer.objects.get_or_create(user=user)
        url = "/api/v1/pets/pets/"
        breed = BreedFactory()

        data = {"name": "Bolinha", "owner": customer.id, "breed": breed.id}

        response = client.post(url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Pet.objects.filter(name="Bolinha").exists()
