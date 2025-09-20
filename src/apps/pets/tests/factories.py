import factory
from factory.faker import Faker as FactoryFaker
from faker import Faker

from src.apps.accounts.tests.factories import CustomerFactory
from src.apps.pets.models import Breed, Pet

fake = Faker("pt_BR")


class BreedFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Breed
        django_get_or_create = ("name",)

    name = factory.Iterator(
        [
            "Golden Retriever",
            "Labrador",
            "Bulldog Francês",
            "Shih Tzu",
            "Poodle",
            "Spitz Alemão",
            "Siamês",
            "Persa",
            "Maine Coon",
            "Angorá",
        ]
    )
    species = factory.Iterator([Breed.Species.DOG, Breed.Species.CAT])
    description = factory.LazyFunction(fake.paragraph)


class PetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Pet

    name = FactoryFaker("first_name", unique=True)
    owner = factory.SubFactory(CustomerFactory)
    breed = factory.SubFactory(BreedFactory)
    birth_date = factory.LazyFunction(
        lambda: fake.date_of_birth(minimum_age=1, maximum_age=15)
    )
