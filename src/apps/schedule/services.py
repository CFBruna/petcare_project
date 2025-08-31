from datetime import date, datetime, time, timedelta

from django.utils import timezone

from .models import Appointment, Service, TimeSlot


def get_available_slots(schedule_date: date, service: Service) -> list[time]:
    now = timezone.now()
    if schedule_date < now.date():
        return []

    day_of_week = schedule_date.weekday()
    working_hours = TimeSlot.objects.filter(day_of_week=day_of_week).order_by(
        "start_time"
    )

    if not working_hours:
        return []

    existing_appointments = (
        Appointment.objects.filter(schedule_time__date=schedule_date)
        .exclude(status=Appointment.Status.CANCELED)
        .select_related("service")
        .order_by("schedule_time")
    )

    occupied_periods = []
    for app in existing_appointments:
        app_start = timezone.localtime(app.schedule_time)
        app_end = app_start + timedelta(minutes=app.service.duration_minutes)
        occupied_periods.append((app_start, app_end))

    available_slots = []
    slot_increment = timedelta(minutes=15)
    service_duration = timedelta(minutes=service.duration_minutes)

    for timeslot in working_hours:
        start_of_day_dt = timezone.make_aware(
            datetime.combine(schedule_date, timeslot.start_time)
        )
        end_of_day_dt = timezone.make_aware(
            datetime.combine(schedule_date, timeslot.end_time)
        )

        current_time = start_of_day_dt
        if schedule_date == now.date() and current_time < now:
            minutes = (now.minute // 15 + 1) * 15
            if minutes >= 60:
                current_time = now.replace(
                    minute=0, second=0, microsecond=0
                ) + timedelta(hours=1)
            else:
                current_time = now.replace(minute=minutes, second=0, microsecond=0)

        while current_time + service_duration <= end_of_day_dt:
            slot_start = current_time
            slot_end = slot_start + service_duration
            is_available = True

            for occupied_start, occupied_end in occupied_periods:
                if max(slot_start, occupied_start) < min(slot_end, occupied_end):
                    is_available = False
                    break

            if is_available:
                available_slots.append(slot_start.time())

            current_time += slot_increment

    return sorted(list(set(available_slots)))
