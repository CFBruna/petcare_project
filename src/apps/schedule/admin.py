from django.contrib import admin

from .forms import AppointmentAdminForm, ServiceAdminForm


class AppointmentAdmin(admin.ModelAdmin):
    form = AppointmentAdminForm
    list_display = ["pet", "service", "schedule_time", "status", "completed_at"]
    list_select_related = ["pet", "service", "pet__owner__user"]
    search_fields = ["pet__name", "service__name"]
    autocomplete_fields = ["pet"]
    list_filter = ["service", "status", "schedule_time"]
    readonly_fields = ["completed_at"]

    class Media:
        js = ("js/schedule_admin.js",)


class ServiceAdmin(admin.ModelAdmin):
    form = ServiceAdminForm
    list_display = ["name", "duration_minutes", "price"]
    search_fields = ["name"]


class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ["get_day_of_week_display", "start_time", "end_time"]
    ordering = ["day_of_week", "start_time"]
