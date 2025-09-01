import random

from django.core.management.base import BaseCommand
from django.db import transaction

from src.apps.accounts.tests.factories import CustomerFactory
from src.apps.health.tests.factories import HealthRecordFactory
from src.apps.pets.tests.factories import PetFactory
from src.apps.schedule.tests.factories import (
    AppointmentFactory,
    ServiceFactory,
    TimeSlotFactory,
)
from src.apps.store.tests.factories import (
    ProductFactory,
    ProductLotFactory,
    SaleFactory,
    SaleItemFactory,
)


class Command(BaseCommand):
    help = "Seeds the database with initial data for development."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting database seeding..."))

        self.stdout.write("Creating services...")
        services = ServiceFactory.create_batch(5)

        self.stdout.write("Creating customers and pets...")
        customers = CustomerFactory.create_batch(10)
        pets = []
        for customer in customers:
            pets.extend(PetFactory.create_batch(random.randint(1, 3), owner=customer))

        self.stdout.write("Creating health records...")
        for pet in pets:
            HealthRecordFactory.create_batch(random.randint(0, 5), pet=pet)

        self.stdout.write("Creating appointments...")
        for pet in pets:
            if random.choice([True, False]):
                AppointmentFactory(pet=pet, service=random.choice(services))

        self.stdout.write("Creating products and lots...")
        products = ProductFactory.create_batch(20)
        lots = []
        for product in products:
            lots.extend(
                ProductLotFactory.create_batch(random.randint(1, 4), product=product)
            )

        self.stdout.write("Creating sales...")
        for _ in range(15):
            sale = SaleFactory(customer=random.choice(customers))
            SaleItemFactory.create_batch(
                random.randint(1, 5), sale=sale, lot=random.choice(lots)
            )

        self.stdout.write("Creating timeslots...")
        days = [0, 1, 2, 3, 4, 5]
        for day in days:
            TimeSlotFactory(day_of_week=day, start_time="09:00", end_time="12:00")
            TimeSlotFactory(day_of_week=day, start_time="14:00", end_time="18:00")

        self.stdout.write(self.style.SUCCESS("Database seeding completed!"))
