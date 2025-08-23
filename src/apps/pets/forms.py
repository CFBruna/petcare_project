# src/apps/pets/forms.py

from django import forms
from django.contrib.auth.models import User
from django.db import transaction

from src.apps.accounts.models import Customer

from .models import Pet


class PetAdminForm(forms.ModelForm):
    new_customer_username = forms.CharField(
        max_length=150,
        required=False,
        label="Nome de Usuário do Novo Dono",
        help_text="Obrigatório se você estiver criando um novo dono.",
    )
    new_customer_first_name = forms.CharField(
        max_length=150,
        required=False,
        label="Nome do Novo Dono",
    )
    new_customer_phone = forms.CharField(
        max_length=25,
        required=False,
        label="Telefone do Novo Dono",
    )

    new_customer_cpf = forms.CharField(
        max_length=14,
        required=False,
        label="CPF do Novo Dono",
    )

    class Meta:
        model = Pet
        fields = ["name", "breed", "birth_date", "owner"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["owner"].required = False

    def clean(self):
        cleaned_data = super().clean()
        owner = cleaned_data.get("owner")
        new_customer_username = cleaned_data.get("new_customer_username")

        if not owner and not new_customer_username:
            self.add_error(
                "owner",
                "Você deve selecionar um dono existente ou preencher os campos do novo dono.",
            )

        if new_customer_username:
            if User.objects.filter(username=new_customer_username).exists():
                self.add_error(
                    "new_customer_username",
                    "Este nome de usuário já existe. Por favor, escolha outro.",
                )

        new_customer_cpf = cleaned_data.get("new_customer_cpf")
        if new_customer_cpf and Customer.objects.filter(cpf=new_customer_cpf).exists():
            self.add_error(
                "new_customer_cpf", "Este CPF já está cadastrado em nosso sistema."
            )

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        new_customer_username = self.cleaned_data.get("new_customer_username")
        new_customer_first_name = self.cleaned_data.get("new_customer_first_name")
        new_customer_phone = self.cleaned_data.get("new_customer_phone")
        new_customer_cpf = self.cleaned_data.get("new_customer_cpf")

        if new_customer_username:
            user = User.objects.create_user(
                username=new_customer_username,
                first_name=new_customer_first_name,
            )
            customer = Customer.objects.create(
                user=user,
                phone=new_customer_phone,
                cpf=new_customer_cpf,
            )

            self.instance.owner = customer

        return super().save(commit)
