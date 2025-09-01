import random
from datetime import timedelta

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from faker import Faker

from src.apps.health.models import HealthRecord
from src.apps.pets.tests.factories import PetFactory

fake = Faker("pt_BR")


class HealthRecordFactory(DjangoModelFactory):
    class Meta:
        model = HealthRecord

    pet = factory.SubFactory(PetFactory)
    record_type = factory.Iterator(
        HealthRecord.RecordType.choices, getter=lambda c: c[0]
    )
    record_date = factory.LazyFunction(timezone.now)

    @factory.lazy_attribute
    def description(self):
        if self.record_type == HealthRecord.RecordType.VACCINE:
            return f"Vacina {random.choice(['V10', 'V8', 'Antirrábica'])} - Lote: {fake.ean(8)}"
        if self.record_type == HealthRecord.RecordType.CONSULTATION:
            return f"Consulta de rotina. Dr(a). {fake.name()}."
        return fake.sentence(nb_words=6)

    @factory.lazy_attribute
    def next_due_date(self):
        if self.record_type == HealthRecord.RecordType.VACCINE:
            return self.record_date + timedelta(days=365)
        return None
