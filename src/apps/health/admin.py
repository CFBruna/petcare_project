from django.contrib import admin


class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ["pet", "record_type", "record_date", "next_due_date", "created_by"]
    autocomplete_fields = ["pet"]
    search_fields = ["pet__name"]
    readonly_fields = ["created_by"]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
