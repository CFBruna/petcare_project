from django.contrib import admin

from .models import Appointment, Service


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["pet", "service", "status"]
    search_fields = ["pet__name", "service__name"]
    list_filter = ["service", "status"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "duration_minutes", "price"]
    search_fields = ["name"]
