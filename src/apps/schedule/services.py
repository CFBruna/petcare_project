from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING

from django.utils import timezone

from .models import Appointment, TimeSlot

if TYPE_CHECKING:
    from src.apps.pets.models import Pet

    from .models import Service


class AppointmentService:
    @staticmethod
    def prepare_appointment_instance(
        *,
        appointment: Appointment,
        pet: Pet,
        service: Service,
        schedule_time: datetime,
        status: str,
        notes: str,
    ) -> Appointment:
        """
        Applies business logic to an appointment instance without saving it.
        """
        is_new = appointment.pk is None
        time_changed = not is_new and appointment.schedule_time != schedule_time

        if is_new or time_changed:
            if schedule_time < timezone.now():
                raise ValueError("Não é possível agendar serviços para o passado.")

        if status == Appointment.Status.COMPLETED and schedule_time > timezone.now():
            raise ValueError(
                "Um agendamento futuro não pode ser marcado como 'Concluído'."
            )

        appointment.pet = pet
        appointment.service = service
        appointment.schedule_time = schedule_time
        appointment.status = status
        appointment.notes = notes

        is_now_completed = status == Appointment.Status.COMPLETED
        was_already_completed = (
            not is_new
            and Appointment.objects.get(pk=appointment.pk).completed_at is not None
        )

        if is_now_completed and not was_already_completed:
            appointment.completed_at = timezone.now()
        elif not is_now_completed and was_already_completed:
            appointment.completed_at = None

        return appointment

    @staticmethod
    def get_available_slots(schedule_date: date, service: "Service") -> list[time]:  # noqa: UP037
        now = timezone.now()
        if schedule_date < now.date():
            return []

        day_of_week: int = schedule_date.weekday()
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

        occupied_periods: list[tuple[datetime, datetime]] = []
        for app in existing_appointments:
            app_start = timezone.localtime(app.schedule_time)
            app_end = app_start + timedelta(minutes=app.service.duration_minutes)
            occupied_periods.append((app_start, app_end))

        available_slots: list[time] = []
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
                minutes_to_add = 15 - (now.minute % 15)
                current_time = (now + timedelta(minutes=minutes_to_add)).replace(
                    second=0, microsecond=0
                )

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
