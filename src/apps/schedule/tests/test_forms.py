from datetime import time, timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from src.apps.schedule.forms import AppointmentAdminForm
from src.apps.schedule.models import Appointment
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
        self.future_date = timezone.now().date() + timedelta(days=7)
        self.past_date = timezone.now().date() - timedelta(days=1)
        self.today = timezone.now().date()

        TimeSlotFactory.create(
            day_of_week=self.future_date.weekday(),
            start_time=time(9, 0),
            end_time=time(12, 0),
        )
        TimeSlotFactory.create(
            day_of_week=self.past_date.weekday(),
            start_time=time(14, 0),
            end_time=time(17, 0),
        )
        TimeSlotFactory.create(
            day_of_week=self.today.weekday(),
            start_time=time(13, 0),
            end_time=time(18, 0),
        )

    def test_form_is_valid_with_correct_data(self):
        form_data = {
            "pet": self.pet.id,
            "service": self.service.id,
            "status": "PENDING",
            "notes": "Test note",
            "appointment_date": self.future_date.isoformat(),
            "appointment_time": "09:00",
        }
        form = AppointmentAdminForm(data=form_data)
        assert form.is_valid(), form.errors

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
            "appointment_date": self.future_date.isoformat(),
            "appointment_time": "10:00",
        }
        form = AppointmentAdminForm(data=form_data)
        assert form.is_valid(), form.errors
        expected_dt = timezone.make_aware(
            timezone.datetime.combine(self.future_date, time(10, 0))
        )
        assert form.cleaned_data["schedule_time"] == expected_dt

    def test_save_method_creates_appointment(self):
        form_data = {
            "pet": self.pet.id,
            "service": self.service.id,
            "status": "CONFIRMED",
            "notes": "A note for the appointment.",
            "appointment_date": self.future_date.isoformat(),
            "appointment_time": "11:00",
        }
        form = AppointmentAdminForm(data=form_data)
        assert form.is_valid(), form.errors
        appointment = form.save()
        assert appointment.pk is not None
        assert appointment.status == "CONFIRMED"
        assert appointment.notes == "A note for the appointment."
        assert appointment.schedule_time.date() == self.future_date

    def test_form_initialization_with_instance(self):
        appointment_time = timezone.make_aware(
            timezone.datetime.combine(self.future_date, time(9, 0))
        )
        appointment = AppointmentFactory(
            schedule_time=appointment_time, service=self.service
        )
        form = AppointmentAdminForm(instance=appointment)
        assert form.fields["appointment_date"].initial == self.future_date.isoformat()
        assert form.fields["appointment_time"].initial == "09:00"
        assert ("09:00", "09:00") in form.fields["appointment_time"].choices

    def test_dynamic_time_choices_are_loaded(self):
        form_data = {
            "service": self.service.id,
            "appointment_date": self.future_date.isoformat(),
        }
        form = AppointmentAdminForm(data=form_data)
        form.is_valid()
        assert len(form.fields["appointment_time"].choices) > 0
        assert ("09:00", "09:00") in form.fields["appointment_time"].choices
        assert ("10:00", "10:00") in form.fields["appointment_time"].choices
        assert ("11:00", "11:00") in form.fields["appointment_time"].choices
        assert ("12:00", "12:00") not in form.fields["appointment_time"].choices

    def test_form_prevents_retroactive_appointments_on_create(self):
        form_data = {
            "pet": self.pet.id,
            "service": self.service.id,
            "status": "PENDING",
            "appointment_date": self.past_date.isoformat(),
            "appointment_time": "15:00",
        }
        form = AppointmentAdminForm(data=form_data)
        assert not form.is_valid()
        assert (
            "Faça uma escolha válida. 15:00 não é uma das escolhas disponíveis."
            in str(form.errors)
        )

    def test_save_sets_completed_at_on_status_change(self):
        appointment_time = timezone.make_aware(
            timezone.datetime.combine(self.past_date, time(14, 30))
        )
        appointment = AppointmentFactory(
            schedule_time=appointment_time,
            status=Appointment.Status.CONFIRMED,
            completed_at=None,
        )

        form_data = {
            "pet": appointment.pet.id,
            "service": appointment.service.id,
            "status": Appointment.Status.COMPLETED,
            "appointment_date": appointment.schedule_time.date().isoformat(),
            "appointment_time": timezone.localtime(appointment.schedule_time).strftime(
                "%H:%M"
            ),
        }
        form = AppointmentAdminForm(data=form_data, instance=appointment)
        assert form.is_valid(), form.errors

        now_fixed = timezone.now()
        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = now_fixed
            form.save()

        appointment.refresh_from_db()
        assert appointment.completed_at is not None
        assert appointment.completed_at == now_fixed

    def test_save_clears_completed_at_when_status_reverted(self):
        appointment_time = timezone.make_aware(
            timezone.datetime.combine(self.past_date, time(15, 0))
        )
        completion_time = timezone.make_aware(
            timezone.datetime.combine(self.past_date, time(15, 30))
        )
        appointment = AppointmentFactory(
            schedule_time=appointment_time,
            status=Appointment.Status.COMPLETED,
            completed_at=completion_time,
        )

        form_data = {
            "pet": appointment.pet.id,
            "service": appointment.service.id,
            "status": Appointment.Status.CONFIRMED,
            "appointment_date": appointment.schedule_time.date().isoformat(),
            "appointment_time": timezone.localtime(appointment.schedule_time).strftime(
                "%H:%M"
            ),
        }
        form = AppointmentAdminForm(data=form_data, instance=appointment)
        assert form.is_valid(), form.errors

        form.save()
        appointment.refresh_from_db()
        assert appointment.completed_at is None

    def test_form_invalid_if_completing_a_future_appointment(self):
        appointment_time = timezone.make_aware(
            timezone.datetime.combine(self.future_date, time(10, 0))
        )
        appointment = AppointmentFactory(schedule_time=appointment_time)

        form_data = {
            "pet": appointment.pet.id,
            "service": appointment.service.id,
            "status": Appointment.Status.COMPLETED,
            "appointment_date": appointment.schedule_time.date().isoformat(),
            "appointment_time": timezone.localtime(appointment.schedule_time).strftime(
                "%H:%M"
            ),
        }

        form = AppointmentAdminForm(data=form_data, instance=appointment)
        assert not form.is_valid()
        assert "status" in form.errors
        assert (
            "Um agendamento futuro não pode ser marcado como 'Concluído'."
            in form.errors["status"][0]
        )
