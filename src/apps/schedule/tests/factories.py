from datetime import time

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from src.apps.pets.tests.factories import PetFactory
from src.apps.schedule.models import Appointment, Service, TimeSlot


class ServiceFactory(DjangoModelFactory):
    class Meta:
        model = Service

    name = factory.Sequence(lambda n: f"Serviço {n}")
    price = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    duration_minutes = 30


class AppointmentFactory(DjangoModelFactory):
    class Meta:
        model = Appointment

    pet = factory.SubFactory(PetFactory)
    service = factory.SubFactory(ServiceFactory)
    schedule_time = factory.LazyFunction(timezone.now)
    status = Appointment.Status.PENDING


class TimeSlotFactory(DjangoModelFactory):
    class Meta:
        model = TimeSlot

    day_of_week = 0
    start_time = time(9, 0)
    end_time = time(18, 0)
