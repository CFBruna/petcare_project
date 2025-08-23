from datetime import date, time
from unittest.mock import patch

import pytest
from django.utils import timezone

from src.apps.schedule.services import get_available_slots
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
            "src.apps.schedule.services.timezone.now", return_value=mock_now_yesterday
        )
        self.patcher.start()

    def teardown_method(self):
        self.patcher.stop()

    def test_get_slots_on_empty_day(self):
        slots = get_available_slots(self.test_date, self.service_30_min)
        assert len(slots) > 0
        assert time(8, 0) in slots
        assert time(11, 30) in slots
        assert time(11, 45) not in slots

    def test_get_slots_for_non_working_day(self):
        non_working_day = date(2025, 8, 17)
        slots = get_available_slots(non_working_day, self.service_30_min)
        assert len(slots) == 0

    def test_slots_are_correct_after_one_appointment(self):
        appointment_time = timezone.make_aware(
            timezone.datetime.combine(self.test_date, time(9, 0))
        )
        AppointmentFactory(service=self.service_60_min, schedule_time=appointment_time)
        slots = get_available_slots(self.test_date, self.service_30_min)
        assert time(8, 0) in slots
        assert time(8, 45) not in slots
        assert time(9, 0) not in slots
        assert time(9, 30) not in slots
        assert time(10, 0) in slots

    def test_scenario_from_debugging_session(self):
        appointment_time = timezone.make_aware(
            timezone.datetime.combine(self.test_date, time(8, 0))
        )
        AppointmentFactory(service=self.service_120_min, schedule_time=appointment_time)
        slots_for_long_service = get_available_slots(
            self.test_date, self.service_120_min
        )
        assert time(8, 0) not in slots_for_long_service
        assert time(10, 0) in slots_for_long_service
        assert time(10, 15) not in slots_for_long_service
        slots_for_short_service = get_available_slots(
            self.test_date, self.service_30_min
        )
        assert time(10, 0) in slots_for_short_service
        assert time(11, 30) in slots_for_short_service

    def test_get_slots_for_today_only_shows_future_slots(self):
        today = self.test_date
        mock_now_today = timezone.make_aware(
            timezone.datetime.combine(today, time(9, 10))
        )

        with patch(
            "src.apps.schedule.services.timezone.now", return_value=mock_now_today
        ):
            slots = get_available_slots(today, self.service_30_min)

        assert time(8, 0) not in slots
        assert time(8, 30) not in slots
        assert time(9, 0) not in slots

        assert time(9, 15) in slots
        assert time(10, 0) in slots
        assert time(11, 30) in slots

    def test_get_slots_for_past_date(self):
        past_date = date(2025, 1, 1)
        slots = get_available_slots(past_date, self.service_30_min)
        assert len(slots) == 0
