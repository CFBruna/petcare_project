from datetime import datetime

from django import forms
from django.utils import timezone

from .models import Appointment, Service
from .services import AppointmentService


class ServiceAdminForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = "__all__"

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            normalized_name = name.strip().title()
            query = Service.objects.filter(name__iexact=normalized_name)
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise forms.ValidationError(
                    "Um serviço com este nome já existe. Por favor, verifique a lista."
                )
            return normalized_name
        return name


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
        fields = ["pet", "service", "status", "notes"]

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
                available_times = AppointmentService.get_available_slots(
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
        available_times = AppointmentService.get_available_slots(date, service)
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
            try:
                AppointmentService.prepare_appointment_instance(
                    appointment=self.instance,
                    pet=cleaned_data.get("pet"),
                    service=cleaned_data.get("service"),
                    schedule_time=cleaned_data.get("schedule_time"),
                    status=cleaned_data.get("status"),
                    notes=cleaned_data.get("notes"),
                )
            except ValueError as e:
                raise forms.ValidationError(str(e)) from e

        return cleaned_data

    def save(self, commit=True):
        self.instance = AppointmentService.prepare_appointment_instance(
            appointment=self.instance,
            pet=self.cleaned_data.get("pet"),
            service=self.cleaned_data.get("service"),
            schedule_time=self.cleaned_data.get("schedule_time"),
            status=self.cleaned_data.get("status"),
            notes=self.cleaned_data.get("notes"),
        )
        return super().save(commit=commit)
