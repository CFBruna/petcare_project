from django.db import models

from src.apps.accounts.models import Customer


class Breed(models.Model):
    class Species(models.TextChoices):
        DOG = "DOG", "Cachorro"
        CAT = "CAT", "Gato"
        BIRD = "BIRD", "Pássaro"
        OTHER = "OTHER", "Outro"

    name = models.CharField(max_length=100, unique=True, verbose_name="Nome da Raça")
    species = models.CharField(
        max_length=10, choices=Species.choices, verbose_name="Espécie"
    )
    description = models.TextField(
        blank=True, help_text="Breve descrição e características da raça."
    )

    class Meta:
        ordering = ["species", "name"]
        verbose_name = "Raça"
        verbose_name_plural = "Raças"

    def __str__(self):
        return self.name


class Pet(models.Model):
    owner = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="pets", verbose_name="Dono"
    )
    name = models.CharField(max_length=100, verbose_name="Nome do Pet")
    breed = models.ForeignKey(Breed, on_delete=models.PROTECT, verbose_name="Raça")
    birth_date = models.DateField(
        blank=True, null=True, verbose_name="Data de Nascimento"
    )

    class Meta:
        verbose_name = "Pet"
        verbose_name_plural = "Pets"

    def __str__(self):
        return f"{self.name} - {self.breed}"
