from datetime import date, time, timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from src.apps.schedule.models import Appointment
from src.apps.schedule.services import AppointmentService
from src.apps.schedule.tests.factories import (
    AppointmentFactory,
    ServiceFactory,
    TimeSlotFactory,
)


@pytest.mark.django_db
class TestAvailableSlotsService:
    def setup_method(self):
        self.test_date = date(2025, 8, 18)
        self.service_30_min = ServiceFactory(duration_minutes=30)
        self.service_60_min = ServiceFactory(duration_minutes=60)
        self.service_120_min = ServiceFactory(duration_minutes=120)
        TimeSlotFactory(day_of_week=0, start_time=time(8, 0), end_time=time(12, 0))

        mock_now_yesterday = timezone.make_aware(timezone.datetime(2025, 8, 17, 10, 0))
        self.patcher = patch(
            "django.utils.timezone.now", return_value=mock_now_yesterday
        )
        self.patcher.start()

    def teardown_method(self):
        self.patcher.stop()

    def test_get_slots_on_empty_day(self):
        slots = AppointmentService.get_available_slots(
            self.test_date, self.service_30_min
        )
        slot_times = [dt.time() for dt in slots]
        assert time(8, 0) in slot_times
        assert time(11, 30) in slot_times
        assert time(11, 45) not in slot_times

    def test_get_slots_for_non_working_day(self):
        non_working_day = date(2025, 8, 17)
        slots = AppointmentService.get_available_slots(
            non_working_day, self.service_30_min
        )
        assert len(slots) == 0

    def test_slots_are_correct_after_one_appointment(self):
        appointment_time = timezone.make_aware(
            timezone.datetime.combine(self.test_date, time(9, 0))
        )
        AppointmentFactory(
            service=self.service_60_min,
            schedule_time=appointment_time,
            status=Appointment.Status.CONFIRMED,
        )
        slots = AppointmentService.get_available_slots(
            self.test_date, self.service_30_min
        )
        slot_times = [dt.time() for dt in slots]
        assert time(8, 45) not in slot_times
        assert time(9, 0) not in slot_times
        assert time(9, 30) not in slot_times
        assert time(10, 0) in slot_times

    def test_scenario_from_debugging_session(self):
        appointment_time = timezone.make_aware(
            timezone.datetime.combine(self.test_date, time(8, 0))
        )
        AppointmentFactory(
            service=self.service_120_min,
            schedule_time=appointment_time,
            status=Appointment.Status.CONFIRMED,
        )
        slots_for_short_service = AppointmentService.get_available_slots(
            self.test_date, self.service_30_min
        )
        slot_times = [dt.time() for dt in slots_for_short_service]
        assert time(8, 0) not in slot_times
        assert time(9, 45) not in slot_times
        assert time(10, 0) in slot_times

    def test_get_slots_for_today_only_shows_future_slots(self):
        today = self.test_date
        mock_now_today = timezone.make_aware(
            timezone.datetime.combine(today, time(9, 10))
        )
        with patch("django.utils.timezone.now", return_value=mock_now_today):
            slots = AppointmentService.get_available_slots(today, self.service_30_min)

        slot_times = [dt.time() for dt in slots]
        assert time(9, 0) not in slot_times
        assert time(9, 15) in slot_times

    def test_get_slots_for_past_date(self):
        past_date = date(2025, 1, 1)
        slots = AppointmentService.get_available_slots(past_date, self.service_30_min)
        assert len(slots) == 0

    def test_prepare_appointment_instance_time_changed(self):
        appointment = AppointmentFactory(
            schedule_time=timezone.now() + timedelta(days=2),
            status=Appointment.Status.CONFIRMED,
        )
        new_time = timezone.now() + timedelta(days=3)
        instance = AppointmentService.prepare_appointment_instance(
            appointment=appointment,
            pet=appointment.pet,
            service=appointment.service,
            schedule_time=new_time,
            status=appointment.status,
            notes=appointment.notes,
        )
        assert instance.schedule_time == new_time

    def test_cancel_appointment_success(self):
        future_time = timezone.now() + timedelta(hours=2)
        appointment = AppointmentFactory(
            schedule_time=future_time, status=Appointment.Status.CONFIRMED
        )

        class MockUser:
            is_staff = False
            is_superuser = False

        canceled_appt = AppointmentService.cancel_appointment(
            appointment, user=MockUser()
        )
        assert canceled_appt.status == Appointment.Status.CANCELED

    def test_cancel_appointment_too_late(self):
        near_future_time = timezone.now() + timedelta(minutes=59)
        appointment = AppointmentFactory(
            schedule_time=near_future_time, status=Appointment.Status.CONFIRMED
        )

        class MockUser:
            is_staff = False
            is_superuser = False

        with pytest.raises(
            ValueError,
            match="Não é possível cancelar o agendamento com menos de 1h de antecedência.",
        ):
            AppointmentService.cancel_appointment(appointment, user=MockUser())

    def test_admin_can_bypass_cancel_restriction(self):
        near_future_time = timezone.now() + timedelta(minutes=10)
        appointment = AppointmentFactory(
            schedule_time=near_future_time, status=Appointment.Status.CONFIRMED
        )

        class MockAdmin:
            is_staff = True
            is_superuser = False

        canceled_appt = AppointmentService.cancel_appointment(
            appointment, user=MockAdmin()
        )
        assert canceled_appt.status == Appointment.Status.CANCELED
