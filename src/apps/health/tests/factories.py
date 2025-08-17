import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from src.apps.health.models import HealthRecord
from src.apps.pets.tests.factories import PetFactory


class HealthRecordFactory(DjangoModelFactory):
    class Meta:
        model = HealthRecord

    pet = factory.SubFactory(PetFactory)
    record_type = HealthRecord.RecordType.VACCINE
    description = factory.Faker("text", max_nb_chars=100)
    record_date = factory.LazyFunction(timezone.now)
