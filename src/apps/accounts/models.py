from django.contrib.auth.models import User
from django.db import models


class Customer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="customer_profile",
        verbose_name="Usuário",
    )
    cpf = models.CharField(
        max_length=14, unique=True, null=True, blank=True, verbose_name="CPF"
    )
    phone = models.CharField(max_length=25, blank=True, verbose_name="Telefone")
    address = models.CharField(max_length=250, blank=True, verbose_name="Endereço")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    @property
    def full_name(self):
        return self.user.get_full_name()

    def __str__(self):
        if self.cpf:
            return f"{self.full_name or self.user.username} - {self.cpf}"
        return self.full_name or self.user.username
