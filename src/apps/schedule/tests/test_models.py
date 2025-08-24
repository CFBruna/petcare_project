from datetime import time

import pytest
from django.utils import timezone

from .factories import AppointmentFactory, ServiceFactory, TimeSlotFactory


@pytest.mark.django_db
class TestScheduleModels:
    def test_service_str(self):
        service = ServiceFactory(name="Banho e Tosa")
        assert str(service) == "Banho E Tosa"

    def test_timeslot_str(self):
        timeslot = TimeSlotFactory(
            day_of_week=3, start_time=time(9, 0), end_time=time(18, 0)
        )
        assert str(timeslot) == "Quinta-feira de 09:00 às 18:00"

    def test_appointment_str(self):
        appointment_time = timezone.make_aware(timezone.datetime(2025, 8, 14, 10, 0))
        appointment = AppointmentFactory(
            pet__name="Rex", schedule_time=appointment_time
        )
        assert str(appointment) == "Agendamento para Rex em 14/08/2025 ás 10:00"
