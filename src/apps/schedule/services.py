from datetime import datetime, timedelta

from django.utils import timezone

from .models import Appointment, Service, TimeSlot


def get_available_slots(date: datetime.date, service: Service) -> list[datetime.time]:
    day_of_week = date.weekday()
    working_hours = TimeSlot.objects.filter(day_of_week=day_of_week)

    if not working_hours.exists():
        return []

    existing_appointments = Appointment.objects.filter(schedule_time__date=date)
    available_slots = []
    service_duration = timedelta(minutes=service.duration_minutes)

    for wh in working_hours:
        start_dt_naive = datetime.combine(date, wh.start_time)
        end_dt_naive = datetime.combine(date, wh.end_time)

        current_time = timezone.make_aware(start_dt_naive)
        end_time = timezone.make_aware(end_dt_naive)

        while current_time + service_duration <= end_time:
            is_available = True

            for app in existing_appointments:
                app_start = app.schedule_time
                app_end = app_start + timedelta(minutes=app.service.duration_minutes)

                if (current_time < app_end) and (
                    app_start < current_time + service_duration
                ):
                    is_available = False
                    break

            if is_available:
                available_slots.append(current_time.time())

            current_time += timedelta(minutes=15)

    return available_slots
