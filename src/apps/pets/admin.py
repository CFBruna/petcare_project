from django.contrib import admin

from .forms import BreedAdminForm, PetAdminForm
from .models import Breed, Pet


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    form = BreedAdminForm
    list_display = ["name", "species"]
    search_fields = ["name"]
    list_filter = ["species"]


@admin.register(Pet)
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
