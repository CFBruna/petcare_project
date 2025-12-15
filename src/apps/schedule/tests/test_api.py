from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from src.apps.pets.tests.factories import PetFactory
from src.apps.schedule.models import Appointment
from src.apps.schedule.services import AppointmentService

from .factories import AppointmentFactory, ServiceFactory, TimeSlotFactory


@pytest.mark.django_db
class TestAvailableSlotsAPI:
    def setup_method(self):
        self.url = reverse("schedule:available-slots")
        self.service = ServiceFactory(duration_minutes=60)
        self.future_date = timezone.now().date() + timedelta(days=7)
        TimeSlotFactory(
            day_of_week=self.future_date.weekday(), start_time="09:00", end_time="12:00"
        )

    def test_get_available_slots_successfully(self, authenticated_client):
        client, _ = authenticated_client
        url = f"{self.url}?date={self.future_date.isoformat()}&service_id={self.service.id}"

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "09:00" in response.data
        assert "10:00" in response.data
        assert "11:00" in response.data
        assert "12:00" not in response.data

    def test_get_slots_missing_params_fails(self, authenticated_client):
        client, _ = authenticated_client
        response = client.get(f"{self.url}?date={self.future_date.isoformat()}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_slots_invalid_date_fails(self, authenticated_client):
        client, _ = authenticated_client
        url = f"{self.url}?date=invalid-date&service_id={self.service.id}"
        response = client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_slots_invalid_service_id(self, authenticated_client):
        client, _ = authenticated_client
        invalid_service_id = 9999
        url = f"{self.url}?date={self.future_date.isoformat()}&service_id={invalid_service_id}"
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAppointmentAPI:
    def setup_method(self):
        self.url = reverse("schedule:appointment-list")
        self.future_date = timezone.now().date() + timedelta(days=7)
        TimeSlotFactory(
            day_of_week=self.future_date.weekday(),
            start_time="13:00",
            end_time="17:00",
        )

    def test_unauthenticated_user_cannot_access_appointments(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_can_list_only_their_appointments(self, regular_user_client):
        client, user = regular_user_client
        my_pet = PetFactory(owner__user=user)
        AppointmentFactory.create_batch(2, pet=my_pet)
        AppointmentFactory()
        response = client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 2

    def test_user_can_create_appointment_for_their_pet(self, authenticated_client):
        client, user = authenticated_client
        my_pet = PetFactory(owner__user=user)
        service = ServiceFactory(duration_minutes=30)

        available_slots = AppointmentService.get_available_slots(
            self.future_date, service
        )
        assert len(available_slots) > 0

        valid_slot = available_slots[0]

        data = {
            "pet": my_pet.id,
            "service": service.id,
            "schedule_date": valid_slot.date().isoformat(),
            "schedule_time_input": valid_slot.strftime("%H:%M"),
        }
        response = client.post(self.url, data=data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Appointment.objects.filter(pet__owner__user=user).count() == 1

    def test_user_cannot_access_other_users_appointment_detail(
        self, regular_user_client
    ):
        client, _ = regular_user_client
        other_appointment = AppointmentFactory()
        detail_url = reverse(
            "schedule:appointment-detail", kwargs={"pk": other_appointment.id}
        )
        response = client.get(detail_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_cannot_delete_other_users_appointment(self, regular_user_client):
        client, _ = regular_user_client
        other_appointment = AppointmentFactory()
        detail_url = reverse(
            "schedule:appointment-detail", kwargs={"pk": other_appointment.id}
        )
        response = client.delete(detail_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
