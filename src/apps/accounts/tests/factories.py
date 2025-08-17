import factory
from django.contrib.auth.models import User

from src.apps.accounts.models import Customer


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    user = factory.SubFactory(UserFactory)
    cpf = factory.Faker("ssn")
    phone = factory.Faker("phone_number")
    address = factory.Faker("address")
