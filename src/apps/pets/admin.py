from django.contrib import admin

from .models import Breed, Pet


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    list_display = ["name", "species"]
    search_fields = ["name"]
    list_filter = ["species"]


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ["name", "breed", "birth_date", "owner"]
    search_fields = [
        "name",
        "breed__name",
        "owner__user__first_name",
        "owner__user__username",
    ]
    list_filter = ["breed__name"]
