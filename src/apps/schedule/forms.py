from datetime import datetime

from django import forms
from django.utils import timezone

from .models import Appointment, Service
from .services import get_available_slots


class AppointmentAdminForm(forms.ModelForm):
    appointment_date = forms.DateField(
        label="Data do Agendamento",
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Selecione primeiro a data para ver os horários disponíveis.",
        required=True,
    )
    appointment_time = forms.ChoiceField(
        label="Horário Disponível",
        choices=[],
        help_text="Este campo será preenchido após selecionar um serviço e uma data.",
        required=True,
    )

    class Meta:
        model = Appointment
        fields = ["pet", "service", "status", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get("instance")

        if instance and instance.schedule_time:
            self.fields["appointment_date"].initial = instance.schedule_time.date()
            current_time_choice = instance.schedule_time.strftime("%H:%M")
            valid_choices = self.get_dynamic_time_choices(
                instance.service, instance.schedule_time.date()
            )
            if (current_time_choice, current_time_choice) not in valid_choices:
                valid_choices.append((current_time_choice, current_time_choice))
                valid_choices.sort()

            self.fields["appointment_time"].choices = valid_choices
            self.fields["appointment_time"].initial = current_time_choice

        elif self.data:
            service = self.data.get("service")
            date_str = self.data.get("appointment_date")
            if service and date_str:
                try:
                    service_instance = Service.objects.get(pk=service)
                    date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    self.fields[
                        "appointment_time"
                    ].choices = self.get_dynamic_time_choices(service_instance, date)
                except (ValueError, Service.DoesNotExist):
                    pass

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

            if cleaned_data["schedule_time"] < timezone.now():
                raise forms.ValidationError(
                    {
                        "__all__": "Não é possível agendar serviços para o passado. Selecione uma data e hora futuras."
                    }
                )

        return cleaned_data

    def save(self, commit=True):
        self.instance.schedule_time = self.cleaned_data.get("schedule_time")
        return super().save(commit)
