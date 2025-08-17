import factory

from src.apps.accounts.tests.factories import CustomerFactory
from src.apps.pets.models import Breed, Pet


class BreedFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Breed

    name = factory.Sequence(lambda n: f"Raça {n}")
    species = factory.Iterator([Breed.Species.DOG, Breed.Species.CAT])


class PetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Pet

    name = factory.Faker("first_name")
    owner = factory.SubFactory(CustomerFactory)
    breed = factory.SubFactory(BreedFactory)
