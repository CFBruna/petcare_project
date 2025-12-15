from django.contrib import admin, messages

from .forms import BreedAdminForm, PetAdminForm


class BreedAdmin(admin.ModelAdmin):
    form = BreedAdminForm
    list_display = ["name", "species"]
    search_fields = ["name"]
    list_filter = ["species"]


class HealthRecordInline(admin.TabularInline):
    from src.apps.health.models import HealthRecord

    model = HealthRecord
    extra = 0
    ordering = ["-record_date"]
    fields = ["record_type", "description", "record_date", "next_due_date"]


class PetAdmin(admin.ModelAdmin):
    form = PetAdminForm
    list_display = ["name", "breed", "birth_date", "owner"]
    search_fields = [
        "name",
        "owner__user__first_name",
        "owner__user__last_name",
        "owner__cpf",
    ]
    list_filter = ["breed__name"]
    autocomplete_fields = ["owner"]
    actions = ["analyze_health_patterns"]
    inlines = [HealthRecordInline]
    fieldsets = (
        (None, {"fields": ("name", "breed", "birth_date", "owner")}),
        (
            "Adicionar Novo Tutor",
            {
                "fields": (
                    "new_customer_username",
                    "new_customer_first_name",
                    "new_customer_phone",
                    "new_customer_cpf",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.action(description="🩺 Analisar Padrões de Saúde (IA)")
    def analyze_health_patterns(self, request, queryset):
        """Analyze health patterns for selected pets using AI."""
        from src.apps.ai.agents.health_agent import (
            HealthAssistantService,
            HealthInsightRequest,
        )

        service = HealthAssistantService()
        success_count = 0
        error_count = 0

        for pet in queryset:
            try:
                request_dto = HealthInsightRequest(
                    pet_id=pet.id, analysis_period_days=180
                )

                result = service.analyze_pet_health(request_dto, user=request.user)

                # Show summary
                patterns_count = len(result.patterns)
                alerts_count = len(result.alerts)

                self.message_user(
                    request,
                    f"✅ {pet.name}: {patterns_count} padrão(ões) detectado(s), "
                    f"{alerts_count} alerta(s), Score de Saúde: {result.health_score:.0f}/100",
                    messages.SUCCESS,
                )

                success_count += 1

            except Exception as e:
                error_count += 1
                self.message_user(
                    request,
                    f"Erro ao analisar {pet.name}: {str(e)}",
                    messages.ERROR,
                )

        if success_count > 0:
            self.message_user(
                request,
                f"🩺 Análise de saúde concluída para {success_count} pet(s)!",
                messages.SUCCESS,
            )
