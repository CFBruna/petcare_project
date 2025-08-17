from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import Appointment, Service, TimeSlot


def get_available_slots(date: datetime.date, service: Service) -> list[time]:
    day_of_week = date.weekday()
    working_hours = TimeSlot.objects.filter(day_of_week=day_of_week)

    if not working_hours.exists():
        return []

    existing_appointments = (
        Appointment.objects.filter(schedule_time__date=date)
        .exclude(status="CANCELED")
        .order_by("schedule_time")
    )

    available_slots = []
    buffer_minutes = 0
    slot_increment_minutes = 15

    for wh in working_hours:
        potential_slots = []
        start_dt = timezone.make_aware(datetime.combine(date, wh.start_time))
        end_dt = timezone.make_aware(datetime.combine(date, wh.end_time))

        current_time = start_dt
        while current_time < end_dt:
            if current_time + timedelta(minutes=service.duration_minutes) <= end_dt:
                potential_slots.append(current_time)
            current_time += timedelta(minutes=slot_increment_minutes)

        blocked_periods = []
        for app in existing_appointments:
            app_start = app.schedule_time
            app_end = app_start + timedelta(minutes=app.service.duration_minutes)
            app_end_with_buffer = app_end + timedelta(minutes=buffer_minutes)
            blocked_periods.append((app_start, app_end_with_buffer))

        for slot_start in potential_slots:
            slot_end = slot_start + timedelta(minutes=service.duration_minutes)
            is_valid = True
            for blocked_start, blocked_end in blocked_periods:
                if not (slot_end <= blocked_start or slot_start >= blocked_end):
                    is_valid = False
                    break

            if is_valid:
                available_slots.append(slot_start.time())

    return available_slots
