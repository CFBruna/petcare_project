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

    class Meta:
        model = Appointment
        fields = [
            "id",
            "pet",
            "pet_name",
            "service",
            "service_name",
            "schedule_time",
            "status",
            "notes",
        ]
        read_only_fields = ["status"]
