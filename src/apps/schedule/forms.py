from datetime import datetime

from django import forms
from django.utils import timezone

from .models import Appointment, Service
from .services import get_available_slots


class AppointmentAdminForm(forms.ModelForm):
    appointment_date = forms.DateField(
        label="Data do Agendamento",
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Selecione a data para ver os horários disponíveis.",
        required=True,
    )
    appointment_time = forms.ChoiceField(
        label="Horário do Agendamento",
        choices=[],
        help_text="Este campo será preenchido após selecionar uma data e um serviço.",
        required=True,
    )

    class Meta:
        model = Appointment
        fields = ["pet", "service", "status", "notes", "completed_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")

        if self.data:
            service_id = self.data.get("service")
            date_str = self.data.get("appointment_date")
            if service_id and date_str:
                try:
                    service = Service.objects.get(pk=service_id)
                    date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    choices = self.get_dynamic_time_choices(service, date)

                    if instance and instance.pk:
                        original_time_str = timezone.localtime(
                            instance.schedule_time
                        ).strftime("%H:%M")
                        if (original_time_str, original_time_str) not in choices:
                            choices.append((original_time_str, original_time_str))
                            choices.sort()

                    self.fields["appointment_time"].choices = choices
                except (ValueError, Service.DoesNotExist):
                    pass
        elif instance and instance.schedule_time:
            local_schedule_time = timezone.localtime(instance.schedule_time)
            self.fields[
                "appointment_date"
            ].initial = local_schedule_time.date().isoformat()
            current_time_choice = local_schedule_time.strftime("%H:%M")

            try:
                available_times = get_available_slots(
                    local_schedule_time.date(), instance.service
                )
                valid_choices = [
                    (t.strftime("%H:%M"), t.strftime("%H:%M")) for t in available_times
                ]
                if (current_time_choice, current_time_choice) not in valid_choices:
                    valid_choices.append((current_time_choice, current_time_choice))
                    valid_choices.sort()

                self.fields["appointment_time"].choices = valid_choices
                self.fields["appointment_time"].initial = current_time_choice
            except Service.DoesNotExist:
                self.fields["appointment_time"].choices = [
                    (current_time_choice, current_time_choice)
                ]
                self.fields["appointment_time"].initial = current_time_choice

    def get_dynamic_time_choices(self, service, date):
        available_times = get_available_slots(date, service)
        return [(t.strftime("%H:%M"), t.strftime("%H:%M")) for t in available_times]

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get("appointment_date")
        time_str = cleaned_data.get("appointment_time")

        if date and time_str:
            hour, minute = map(int, time_str.split(":"))
            local_dt = datetime.combine(date, datetime.min.time()).replace(
                hour=hour, minute=minute
            )
            cleaned_data["schedule_time"] = timezone.make_aware(local_dt)

            is_new_appointment = self.instance.pk is None
            schedule_time_changed = False
            if not is_new_appointment:
                if self.instance.schedule_time != cleaned_data["schedule_time"]:
                    schedule_time_changed = True

            if is_new_appointment or schedule_time_changed:
                if cleaned_data["schedule_time"] < timezone.now():
                    self.add_error(
                        "appointment_time",
                        "Não é possível agendar serviços para o passado.",
                    )

            new_status = cleaned_data.get("status")
            if new_status == Appointment.Status.COMPLETED:
                if cleaned_data["schedule_time"] > timezone.now():
                    self.add_error(
                        "status",
                        "Um agendamento futuro não pode ser marcado como 'Concluído'.",
                    )

            if (
                self.instance
                and self.instance.status == Appointment.Status.COMPLETED
                and new_status != Appointment.Status.COMPLETED
            ):
                if "completed_at" in cleaned_data:
                    cleaned_data["completed_at"] = None

        return cleaned_data

    def save(self, commit=True):
        is_completed_status = (
            self.cleaned_data.get("status") == Appointment.Status.COMPLETED
        )

        if is_completed_status and not self.instance.completed_at:
            self.instance.completed_at = timezone.now()

        if (
            self.instance.status == Appointment.Status.COMPLETED
            and not is_completed_status
        ):
            self.instance.completed_at = None

        self.instance.schedule_time = self.cleaned_data.get("schedule_time")
        return super().save(commit)
