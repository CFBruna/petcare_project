import factory
from django.contrib.auth.models import User
from faker import Faker

from src.apps.accounts.models import Customer

fake = Faker("pt_BR")


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.LazyFunction(fake.user_name)
    first_name = factory.LazyFunction(fake.first_name)
    last_name = factory.LazyFunction(fake.last_name)
    email = factory.LazyFunction(fake.email)


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    user = factory.SubFactory(UserFactory)
    cpf = factory.LazyFunction(fake.cpf)
    phone = factory.LazyFunction(fake.phone_number)
    address = factory.LazyFunction(fake.address)
