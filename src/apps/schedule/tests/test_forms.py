from datetime import date, time

import pytest
from django.utils import timezone

from src.apps.schedule.forms import AppointmentAdminForm
from src.apps.schedule.tests.factories import (
    AppointmentFactory,
    PetFactory,
    ServiceFactory,
    TimeSlotFactory,
)


@pytest.mark.django_db
class TestAppointmentAdminForm:
    def setup_method(self):
        self.service = ServiceFactory(duration_minutes=60)
        self.pet = PetFactory()
        self.test_date = date(2025, 8, 21)  # A Thursday
        TimeSlotFactory(day_of_week=3, start_time=time(9, 0), end_time=time(12, 0))

    def test_form_is_valid_with_correct_data(self):
        form_data = {
            "pet": self.pet.id,
            "service": self.service.id,
            "status": "PENDING",
            "notes": "Test note",
            "appointment_date": self.test_date.isoformat(),
            "appointment_time": "09:00",
        }
        form = AppointmentAdminForm(data=form_data)
        assert form.is_valid()

    def test_form_is_invalid_without_required_fields(self):
        form = AppointmentAdminForm(data={})
        assert not form.is_valid()
        assert "pet" in form.errors
        assert "service" in form.errors
        assert "appointment_date" in form.errors

    def test_clean_method_creates_schedule_time(self):
        form_data = {
            "pet": self.pet.id,
            "service": self.service.id,
            "status": "PENDING",
            "appointment_date": self.test_date.isoformat(),
            "appointment_time": "10:00",
        }
        form = AppointmentAdminForm(data=form_data)
        assert form.is_valid(), form.errors
        expected_dt = timezone.make_aware(timezone.datetime(2025, 8, 21, 10, 0))
        assert form.cleaned_data["schedule_time"] == expected_dt

    def test_save_method_creates_appointment(self):
        form_data = {
            "pet": self.pet.id,
            "service": self.service.id,
            "status": "CONFIRMED",
            "notes": "A note for the appointment.",
            "appointment_date": self.test_date.isoformat(),
            "appointment_time": "11:00",
        }
        form = AppointmentAdminForm(data=form_data)
        assert form.is_valid(), form.errors
        appointment = form.save()
        assert appointment.pk is not None
        assert appointment.status == "CONFIRMED"
        assert appointment.notes == "A note for the appointment."
        assert appointment.schedule_time.year == 2025

    def test_form_initialization_with_instance(self):
        appointment_time = timezone.make_aware(timezone.datetime(2025, 8, 21, 9, 0))
        appointment = AppointmentFactory(
            schedule_time=appointment_time, service=self.service
        )
        form = AppointmentAdminForm(instance=appointment)
        assert form.fields["appointment_date"].initial == self.test_date
        assert form.fields["appointment_time"].initial == "09:00"
        assert ("09:00", "09:00") in form.fields["appointment_time"].choices

    def test_dynamic_time_choices_are_loaded(self):
        # Simulate the dynamic request that populates the time choices
        form_data = {
            "service": self.service.id,
            "appointment_date": self.test_date.isoformat(),
        }
        form = AppointmentAdminForm(data=form_data)
        assert len(form.fields["appointment_time"].choices) > 0
        assert ("09:00", "09:00") in form.fields["appointment_time"].choices
        assert ("10:00", "10:00") in form.fields["appointment_time"].choices
        assert ("11:00", "11:00") in form.fields["appointment_time"].choices
        assert ("12:00", "12:00") not in form.fields["appointment_time"].choices
