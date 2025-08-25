from datetime import datetime

from rest_framework import serializers

from .models import Appointment, Service, TimeSlot
from .services import get_available_slots


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

    schedule_date = serializers.DateField(write_only=True)
    schedule_time = serializers.TimeField(write_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "pet",
            "pet_name",
            "service",
            "service_name",
            "status",
            "notes",
            "schedule_date",
            "schedule_time",
        ]
        read_only_fields = ["status"]

    def validate(self, data):
        schedule_date = data.get("schedule_date")
        schedule_time = data.get("schedule_time")
        service = data.get("service")

        combined_datetime = datetime.combine(schedule_date, schedule_time)

        available_slots = get_available_slots(schedule_date, service)

        if combined_datetime.time() not in available_slots:
            raise serializers.ValidationError(
                "O horário e/ou a data selecionados não estão disponíveis."
            )

        data["schedule_time"] = combined_datetime

        return data

    def create(self, validated_data):
        schedule_time = validated_data.pop("schedule_time")
        validated_data.pop("schedule_date")

        return Appointment.objects.create(schedule_time=schedule_time, **validated_data)
