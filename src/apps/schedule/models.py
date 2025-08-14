from django.db import models

from src.apps.pets.models import Pet


class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome do Serviço")
    description = models.TextField(blank=True, verbose_name="Descrição")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Preço")
    duration_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Duração do serviço em minutos.",
        verbose_name="Duração em minutos",
    )

    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"

    def __str__(self):
        return self.name


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        CONFIRMED = "CONFIRMED", "Confirmado"
        COMPLETED = "COMPLETED", "Concluído"
        CANCELED = "CANCELED", "Cancelado"

    pet = models.ForeignKey(Pet, on_delete=models.PROTECT, related_name="appointments")
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Serviço",
    )
    schedule_time = models.DateTimeField(verbose_name="Data e Hora do Agendamento")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status",
    )
    notes = models.TextField(
        blank=True,
        help_text="Observações do cliente ou do funcionário.",
        verbose_name="Observações",
    )

    class Meta:
        ordering = ["-schedule_time"]
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"

    def __str__(self):
        formatted_date = self.schedule_time.strftime("%d/%m/%Y ás %H:%M")
        return f"Agendamento para {self.pet.name} em {formatted_date}"


class TimeSlot(models.Model):
    day_of_week = models.IntegerField(
        choices=[
            (0, "Segunda-feira"),
            (1, "Terça-feira"),
            (2, "Quarta-feira"),
            (3, "Quinta-feira"),
            (4, "Sexta-feira"),
            (5, "Sábado"),
            (6, "Domingo"),
        ],
        verbose_name="Dia da Semana",
    )
    start_time = models.TimeField(verbose_name="Início do Horário")
    end_time = models.TimeField(verbose_name="Fim do Horário")

    class Meta:
        verbose_name = "Horário Disponível"
        verbose_name_plural = "Horários Disponíveis"
        unique_together = ("day_of_week", "start_time")
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        return f"{self.get_day_of_week_display()} de {self.start_time.strftime('%H:%M')} às {self.end_time.strftime('%H:%M')}"
