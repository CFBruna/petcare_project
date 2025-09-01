import pytest
from rest_framework import status
from rest_framework.test import APIClient

from src.apps.accounts.models import Customer
from src.apps.accounts.tests.factories import UserFactory
from src.apps.pets.models import Breed, Pet

from .factories import BreedFactory, PetFactory


@pytest.mark.django_db
class TestBreedAPI:
    def test_list_breeds_unauthorized(self, api_client):
        BreedFactory.create_batch(3)
        url = "/api/v1/pets/breeds/"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_breed_unauthorized(self, api_client):
        url = "/api/v1/pets/breeds/"
        data = {"name": "Nova Raça", "species": "DOG"}
        response = api_client.post(url, data=data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

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
    def setup_method(self):
        self.user = UserFactory()
        self.customer = Customer.objects.get_or_create(user=self.user)[0]
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/v1/pets/pets/"
        self.my_pet = PetFactory(owner=self.customer)

    def test_unauthenticated_user_cannot_access_pets(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_can_list_only_their_pets(self):
        PetFactory.create_batch(2, owner=self.customer)
        PetFactory()
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 3

    def test_user_can_create_pet_for_themselves(self):
        breed = BreedFactory()
        data = {"name": "Bolinha", "breed": breed.id}
        response = self.client.post(self.url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        pet = Pet.objects.get(id=response.data["id"])
        assert pet.name == "Bolinha"
        assert pet.owner == self.customer

    def test_user_cannot_access_other_users_pet_detail(self):
        other_pet = PetFactory()
        response = self.client.get(f"{self.url}{other_pet.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_can_update_their_own_pet(self):
        data = {"name": "Fido"}
        response = self.client.patch(f"{self.url}{self.my_pet.id}/", data=data)
        assert response.status_code == status.HTTP_200_OK
        self.my_pet.refresh_from_db()
        assert self.my_pet.name == "Fido"

    def test_user_cannot_update_other_users_pet(self):
        other_pet = PetFactory()
        data = {"name": "Malicious Name"}
        response = self.client.patch(f"{self.url}{other_pet.id}/", data=data)
        assert response.status_code == status.HTTP_404_NOT_FOUND
