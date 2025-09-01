import random
from datetime import time

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from faker import Faker

from src.apps.pets.tests.factories import PetFactory
from src.apps.schedule.models import Appointment, Service, TimeSlot

fake = Faker("pt_BR")


class ServiceFactory(DjangoModelFactory):
    class Meta:
        model = Service
        django_get_or_create = ("name",)

    name = factory.Iterator(
        [
            "Banho e Tosa",
            "Consulta Veterinária",
            "Vacinação",
            "Hidratação",
            "Tosa Higiênica",
        ]
    )
    description = factory.LazyFunction(fake.sentence)
    price = factory.Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        positive=True,
        min_value=30,
        max_value=150,
    )
    duration_minutes = factory.Iterator([30, 45, 60, 90])


class AppointmentFactory(DjangoModelFactory):
    class Meta:
        model = Appointment

    pet = factory.SubFactory(PetFactory)
    service = factory.SubFactory(ServiceFactory)
    schedule_time = factory.LazyFunction(timezone.now)
    status = factory.Iterator([s[0] for s in Appointment.Status.choices])
    notes = factory.LazyFunction(
        lambda: fake.sentence() if random.choice([True, False]) else ""
    )


class TimeSlotFactory(DjangoModelFactory):
    class Meta:
        model = TimeSlot
        django_get_or_create = ("day_of_week", "start_time")

    day_of_week = 0
    start_time = time(9, 0)
    end_time = time(18, 0)
