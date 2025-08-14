from django.contrib import admin

from .forms import AppointmentAdminForm
from .models import Appointment, Service, TimeSlot


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    form = AppointmentAdminForm
    list_display = ["pet", "service", "schedule_time", "status"]
    search_fields = ["pet__name", "service__name"]
    list_filter = ["service", "status", "schedule_time"]

    fieldsets = (
        (None, {"fields": ("pet", "service", "status")}),
        ("Data e Hora", {"fields": ("appointment_date", "appointment_time")}),
        (
            "Observações",
            {
                "fields": ("notes",),
                "classes": ("collapse",),
            },
        ),
    )

    class Media:
        js = ("js/schedule_admin.js",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "duration_minutes", "price"]
    search_fields = ["name"]


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ["get_day_of_week_display", "start_time", "end_time"]
    ordering = ["day_of_week", "start_time"]
