from django.conf import settings
from django.db import models

from src.apps.pets.models import Pet


class HealthRecord(models.Model):
    class RecordType(models.TextChoices):
        VACCINE = "VACCINE", "Vacina"
        SURGERY = "SURGERY", "Cirurgia"
        CONSULTATION = "CONSULTATION", "Consulta"
        NOTE = "NOTE", "Anotação Geral"
        OWNER_NOTE = "OWNER_NOTE", "Anotação do Dono"

    pet = models.ForeignKey(
        Pet, on_delete=models.CASCADE, related_name="health_records"
    )
    record_type = models.CharField(
        max_length=20, choices=RecordType.choices, verbose_name="Tipo de Registro"
    )
    description = models.TextField(
        help_text="Descrição detalhada do evento (Ex: Vacina V10, Lote XYZ)."
    )
    record_date = models.DateField(help_text="Data em que o evento ocorreu.")
    next_due_date = models.DateField(
        blank=True, null=True, help_text="Próxima data (ex: revacinação)."
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="health_records_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-record_date", "-created_at"]
        verbose_name = "Registro de Saúde"
        verbose_name_plural = "Registros de Saúde"

    def __str__(self):
        return f"{self.get_record_type_display()} de {self.pet.name}"
