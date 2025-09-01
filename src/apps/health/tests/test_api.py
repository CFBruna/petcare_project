import pytest
from django.contrib.auth.models import Permission
from rest_framework import status

from src.apps.health.models import HealthRecord
from src.apps.health.tests.factories import HealthRecordFactory
from src.apps.pets.tests.factories import PetFactory

URL = "/api/v1/health/health-records/"


@pytest.mark.django_db
class TestHealthRecordAPI:
    def test_unauthenticated_user_cannot_access(self, api_client):
        response = api_client.get(URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = api_client.post(URL, {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_health_records_for_owned_pets(self, authenticated_client):
        client, user = authenticated_client
        my_pet = PetFactory(owner__user=user)
        HealthRecordFactory.create_batch(2, pet=my_pet)
        HealthRecordFactory()
        response = client.get(URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 2

    def test_create_health_record(self, authenticated_client):
        client, user = authenticated_client
        my_pet = PetFactory(owner__user=user)

        permission = Permission.objects.get(codename="add_healthrecord")
        user.user_permissions.add(permission)

        data = {
            "pet": my_pet.id,
            "record_type": HealthRecord.RecordType.VACCINE,
            "description": "Vacina V10",
            "record_date": "2025-08-14",
        }
        response = client.post(URL, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["created_by_username"] == user.username

    def test_user_cannot_access_other_users_records(self, authenticated_client):
        client, user = authenticated_client
        other_record = HealthRecordFactory()
        response = client.get(f"{URL}{other_record.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        permission_delete = Permission.objects.get(codename="delete_healthrecord")
        user.user_permissions.add(permission_delete)

        response = client.delete(f"{URL}{other_record.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_health_record(self, authenticated_client):
        client, user = authenticated_client
        my_pet = PetFactory(owner__user=user)
        record = HealthRecordFactory(pet=my_pet, description="Initial description")

        permission = Permission.objects.get(codename="change_healthrecord")
        user.user_permissions.add(permission)

        data = {"description": "Updated description"}
        response = client.patch(f"{URL}{record.id}/", data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["description"] == "Updated description"

        record.refresh_from_db()
        assert record.description == "Updated description"

    def test_user_cannot_update_other_users_record(self, authenticated_client):
        client, user = authenticated_client
        other_record = HealthRecordFactory()
        data = {"description": "Malicious update"}
        response = client.patch(f"{URL}{other_record.id}/", data=data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_cannot_delete_other_users_record(self, authenticated_client):
        client, user = authenticated_client
        other_record = HealthRecordFactory()
        response = client.delete(f"{URL}{other_record.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
