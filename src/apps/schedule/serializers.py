from datetime import datetime

from django.utils import timezone
from rest_framework import serializers

from .models import Appointment, Service, TimeSlot


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
    schedule_time_input = serializers.TimeField(write_only=True, source="schedule_time")

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
            "schedule_time_input",
            "schedule_time",
        ]
        read_only_fields = ["status", "schedule_time"]

    def validate(self, data):
        from .services import get_available_slots

        schedule_date = data.get("schedule_date")
        schedule_time = data.get("schedule_time")
        service = data.get("service")

        available_slots = get_available_slots(schedule_date, service)

        if schedule_time not in available_slots:
            raise serializers.ValidationError(
                "The selected time and/or date is not available."
            )

        combined_datetime = datetime.combine(schedule_date, schedule_time)
        aware_datetime = timezone.make_aware(combined_datetime)
        data["schedule_time"] = aware_datetime

        return data

    def create(self, validated_data):
        validated_data.pop("schedule_date")
        return Appointment.objects.create(**validated_data)
