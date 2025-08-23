from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from src.apps.pets.tests.factories import PetFactory
from src.apps.schedule.models import Appointment

from .factories import AppointmentFactory, ServiceFactory, TimeSlotFactory


@pytest.mark.django_db
class TestAvailableSlotsAPI:
    def setup_method(self):
        self.url = "/api/v1/schedule/available-slots/"
        self.service = ServiceFactory(duration_minutes=60)
        self.future_date = timezone.now().date() + timedelta(days=7)
        TimeSlotFactory(
            day_of_week=self.future_date.weekday(), start_time="09:00", end_time="12:00"
        )

    def test_get_available_slots_successfully(self, authenticated_client):
        client, user = authenticated_client
        url = f"{self.url}?date={self.future_date.isoformat()}&service_id={self.service.id}"

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "09:00" in response.data
        assert "10:00" in response.data
        assert "11:00" in response.data
        assert "12:00" not in response.data

    def test_get_slots_missing_params_fails(self, authenticated_client):
        client, user = authenticated_client
        response = client.get(f"{self.url}?date={self.future_date.isoformat()}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_slots_invalid_date_fails(self, authenticated_client):
        client, user = authenticated_client
        url = f"{self.url}?date=invalid-date&service_id={self.service.id}"
        response = client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_slots_invalid_service_id(self, authenticated_client):
        client, user = authenticated_client
        invalid_service_id = 9999
        url = f"{self.url}?date={self.future_date.isoformat()}&service_id={invalid_service_id}"
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAppointmentAPI:
    def setup_method(self):
        self.url = "/api/v1/schedule/appointments/"
        self.future_date = timezone.now().date() + timedelta(days=7)

    def test_unauthenticated_user_cannot_access_appointments(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_can_list_only_their_appointments(self, authenticated_client):
        client, user = authenticated_client
        my_pet = PetFactory(owner__user=user)
        AppointmentFactory.create_batch(2, pet=my_pet)

        AppointmentFactory()

        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 2

    def test_user_can_create_appointment_for_their_pet(self, authenticated_client):
        client, user = authenticated_client
        my_pet = PetFactory(owner__user=user)
        service = ServiceFactory()
        appointment_time = timezone.make_aware(
            timezone.datetime.combine(
                self.future_date, timezone.datetime.min.time()
            ).replace(hour=14, minute=0)
        )

        data = {
            "pet": my_pet.id,
            "service": service.id,
            "schedule_time": appointment_time.isoformat(),
        }
        response = client.post(self.url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Appointment.objects.filter(pet__owner__user=user).count() == 1

    def test_user_cannot_access_other_users_appointment_detail(
        self, authenticated_client
    ):
        client, user = authenticated_client
        other_appointment = AppointmentFactory()

        response = client.get(f"{self.url}{other_appointment.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
