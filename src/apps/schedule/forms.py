from datetime import datetime

from django import forms
from django.db import IntegrityError
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
    appointment_time = forms.CharField(
        label="Horário do Agendamento",
        help_text="Este campo será preenchido após selecionar uma data e um serviço.",
        widget=forms.Select(choices=[]),
        required=True,
    )

    class Meta:
        model = Appointment
        fields = ["pet", "service", "status", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")

        choices = []
        initial_time = None
        initial_date = None

        if self.data or instance:
            service = self._get_service(instance)
            date = self._get_date(instance)

            if service and date:
                choices = self.get_dynamic_time_choices(service, date)
                initial_date = date.isoformat()

        if instance and instance.pk:
            local_schedule_time = timezone.localtime(instance.schedule_time)
            initial_time_str = local_schedule_time.strftime("%H:%M")
            initial_time = initial_time_str
            initial_date = local_schedule_time.date().isoformat()

            if (initial_time_str, initial_time_str) not in choices:
                choices.append((initial_time_str, initial_time_str))
                choices.sort()

        self.fields["appointment_time"].widget.choices = choices
        if initial_time:
            self.initial["appointment_time"] = initial_time
        if initial_date:
            self.initial["appointment_date"] = initial_date

    def _get_service(self, instance):
        if self.data:
            try:
                return Service.objects.get(pk=self.data.get("service"))
            except (Service.DoesNotExist, ValueError):
                return None
        if instance:
            return instance.service
        return None

    def _get_date(self, instance):
        if self.data:
            try:
                return datetime.strptime(
                    self.data.get("appointment_date"), "%Y-%m-%d"
                ).date()
            except (ValueError, TypeError):
                return None
        if instance and instance.schedule_time:
            return timezone.localtime(instance.schedule_time).date()
        return None

    def get_dynamic_time_choices(self, service, date):
        available_times = AppointmentService.get_available_slots(date, service)
        return [(t.strftime("%H:%M"), t.strftime("%H:%M")) for t in available_times]

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get("appointment_date")
        time_str = cleaned_data.get("appointment_time")
        service = cleaned_data.get("service")

        if not (date and time_str and service):
            return cleaned_data

        try:
            submitted_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError as e:
            raise forms.ValidationError(
                {"appointment_time": "Formato de hora inválido."}
            ) from e

        available_datetimes = AppointmentService.get_available_slots(date, service)
        available_times = [dt.time() for dt in available_datetimes]

        is_editing = self.instance and self.instance.pk
        if is_editing:
            original_time = timezone.localtime(self.instance.schedule_time).time()
            if original_time not in available_times:
                available_times.append(original_time)

        if submitted_time not in available_times:
            self.add_error(
                "appointment_time",
                "Este horário não está mais disponível. Por favor, selecione outro.",
            )
            return cleaned_data

        local_dt = datetime.combine(date, submitted_time)
        cleaned_data["schedule_time"] = timezone.make_aware(local_dt)

        try:
            self.instance = AppointmentService.prepare_appointment_instance(
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
        try:
            return super().save(commit=commit)
        except IntegrityError:
            self.add_error(
                "appointment_time",
                "Este horário foi agendado por outra pessoa. Por favor, escolha um novo horário.",
            )
            return self.instance
