import zoneinfo

from rest_framework import serializers

from .models import Appointment, Service, TimeSlot
from .services import AppointmentService


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "description", "price", "duration_minutes"]


class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ["id", "day_of_week", "start_time", "end_time"]


class AppointmentSerializer(serializers.ModelSerializer):
    pet_name = serializers.CharField(source="pet.name", read_only=True)
    service_name = serializers.CharField(source="service.name", read_only=True)
    service_duration = serializers.IntegerField(
        source="service.duration_minutes", read_only=True
    )

    schedule_date = serializers.DateField(write_only=True)
    schedule_time_input = serializers.TimeField(write_only=True, source="schedule_time")

    class Meta:
        model = Appointment
        fields = [
            "id",
            "pet",
            "pet_name",
            "service",
            "service_name",
            "service_duration",
            "status",
            "notes",
            "schedule_date",
            "schedule_time_input",
            "schedule_time",
        ]
        read_only_fields = ["status", "schedule_time"]

    def validate(self, data):
        schedule_date = data.get("schedule_date")
        schedule_time = data.get("schedule_time")
        service = data.get("service")

        if not (schedule_date and schedule_time and service):
            raise serializers.ValidationError(
                "'schedule_date', 'schedule_time_input', e 'service' são obrigatórios."
            )

        available_slots = AppointmentService.get_available_slots(schedule_date, service)
        sao_paulo_tz = zoneinfo.ZoneInfo("America/Sao_Paulo")
        matching_slot = None
        for slot in available_slots:
            slot_local_time = slot.astimezone(sao_paulo_tz).time()
            if slot_local_time == schedule_time:
                matching_slot = slot
                break

        if matching_slot is None:
            available_times_local = [
                slot.astimezone(sao_paulo_tz).strftime("%H:%M")
                for slot in available_slots
            ]
            raise serializers.ValidationError(
                {
                    "schedule_time_input": f"O horário selecionado não está disponível. Horários disponíveis: {available_times_local}"
                }
            )

        data["schedule_time"] = matching_slot
        return data

    def create(self, validated_data):
        validated_data.pop("schedule_date")
        return Appointment.objects.create(**validated_data)
