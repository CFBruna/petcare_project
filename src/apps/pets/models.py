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
        blank=True,
        help_text="Breve descrição e características da raça.",
        verbose_name="Descrição",
    )

    class Meta:
        ordering = ["species", "name"]
        verbose_name = "Raça"
        verbose_name_plural = "Raças"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower().title()
        super().save(*args, **kwargs)


class Pet(models.Model):
    owner = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="pets", verbose_name="Tutor"
    )
    name = models.CharField(max_length=100, verbose_name="Nome do Pet")
    breed = models.ForeignKey(Breed, on_delete=models.PROTECT, verbose_name="Raça")
    birth_date = models.DateField(
        blank=True, null=True, verbose_name="Data de Nascimento"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Pet"
        verbose_name_plural = "Pets"
        unique_together = ("owner", "name")

    def __str__(self):
        owner_name = self.owner.full_name or self.owner.user.username
        return f"{self.name} - Tutor: {owner_name}"
