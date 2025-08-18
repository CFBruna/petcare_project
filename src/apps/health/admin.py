from django.contrib import admin

from .models import HealthRecord


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ["pet", "record_type", "record_date", "created_by"]
    search_fields = ["pet"]
