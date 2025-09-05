from __future__ import annotations

import logging
from typing import Any

from django import forms
from django.contrib.auth.models import User
from django.db import transaction

from src.apps.accounts.models import Customer
from src.apps.accounts.services import CustomerService

from .models import Breed, Pet

logger = logging.getLogger(__name__)


class BreedAdminForm(forms.ModelForm):
    class Meta:
        model = Breed
        fields = "__all__"

    def clean_name(self) -> str:
        name: str = self.cleaned_data["name"]
        normalized_name = name.strip().lower().title()

        query = Breed.objects.filter(name__iexact=normalized_name)
        if self.instance.pk:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise forms.ValidationError(
                "Uma raça com este nome já existe. Por favor, verifique a lista antes de adicionar uma nova."
            )
        return normalized_name


class PetAdminForm(forms.ModelForm):
    new_customer_username = forms.CharField(
        max_length=150,
        required=False,
        label="Nome de Usuário do Novo Tutor",
        help_text="Obrigatório se você estiver criando um novo tutor.",
    )
    new_customer_first_name = forms.CharField(
        max_length=150,
        required=False,
        label="Nome do Novo Tutor",
    )
    new_customer_phone = forms.CharField(
        max_length=25,
        required=False,
        label="Telefone do Novo Tutor",
    )

    new_customer_cpf = forms.CharField(
        max_length=14,
        required=False,
        label="CPF do Novo Tutor",
    )

    class Meta:
        model = Pet
        fields = ["name", "breed", "birth_date", "owner"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["owner"].required = False

    def clean(self) -> dict[str, Any]:
        cleaned_data: dict[str, Any] | None = super().clean()

        if cleaned_data is None:
            return {}

        owner: Customer | None = cleaned_data.get("owner")
        name: str | None = cleaned_data.get("name")
        new_customer_username: str | None = cleaned_data.get("new_customer_username")

        if not owner and not new_customer_username:
            self.add_error(
                "owner",
                "Você deve selecionar um tutor existente ou preencher os campos do novo tutor.",
            )

        if new_customer_username:
            if User.objects.filter(username=new_customer_username).exists():
                self.add_error(
                    "new_customer_username",
                    "Este nome de usuário já existe. Por favor, escolha outro.",
                )

        new_customer_cpf: str | None = cleaned_data.get("new_customer_cpf")
        if new_customer_cpf and Customer.objects.filter(cpf=new_customer_cpf).exists():
            self.add_error(
                "new_customer_cpf", "Este CPF já está cadastrado em nosso sistema."
            )

        if owner and name:
            query = Pet.objects.filter(owner=owner, name__iexact=name)
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise forms.ValidationError(
                    f"O tutor '{owner}' já possui um pet com o nome '{name}'. "
                    "Por favor, escolha um nome diferente."
                )
        return cleaned_data

    @transaction.atomic
    def save(self, commit: bool = True) -> Pet:
        new_customer_username: str | None = self.cleaned_data.get(
            "new_customer_username"
        )

        if new_customer_username:
            customer = CustomerService.create_customer(
                username=new_customer_username,
                first_name=self.cleaned_data.get("new_customer_first_name", ""),
                phone=self.cleaned_data.get("new_customer_phone", ""),
                cpf=self.cleaned_data.get("new_customer_cpf", ""),
            )
            self.instance.owner = customer

        pet: Pet = super().save(commit=commit)
        if commit:
            logger.info(
                "Pet '%s' (ID: %d) for owner '%s' saved via PetAdminForm.",
                pet.name,
                pet.id,
                pet.owner.user.username,
            )
        return pet
