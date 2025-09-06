import random
from datetime import timedelta
from decimal import Decimal

import structlog
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from src.apps.accounts.models import Customer
from src.apps.accounts.tests.factories import CustomerFactory
from src.apps.health.tests.factories import HealthRecordFactory
from src.apps.pets.models import Breed, Pet
from src.apps.pets.tests.factories import BreedFactory, PetFactory
from src.apps.schedule.models import Appointment, Service, TimeSlot
from src.apps.schedule.tests.factories import AppointmentFactory
from src.apps.store.models import Brand, Category, Product, ProductLot, Sale
from src.apps.store.services import SaleService
from src.apps.store.tests.factories import (
    BrandFactory,
    CategoryFactory,
    ProductFactory,
)

logger = structlog.get_logger(__name__)
User = get_user_model()
fake = Faker("pt_BR")


class Command(BaseCommand):
    help = "Seeds the database with a rich and realistic dataset for development."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting database seeding..."))

        self.stdout.write("Creating basic setup data...")
        self._create_timeslots()
        self._create_breeds_and_categories()

        self.stdout.write("Creating services and products...")
        services = self._create_services()
        products = self._create_products()
        self._create_lots(products)

        self.stdout.write("Creating customers and their pets...")
        customers = self._create_customers()
        pets = self._create_pets(customers)

        self.stdout.write("Creating dependent records (health, appointments, sales)...")
        self._create_health_records(pets)
        self._create_appointments(pets, services)
        self._create_sales()

        self.stdout.write(self.style.SUCCESS("Database seeding completed!"))

    def _create_timeslots(self):
        TimeSlot.objects.all().delete()
        days = [0, 1, 2, 3, 4]
        TimeSlot.objects.create(day_of_week=5, start_time="09:00", end_time="13:00")
        for day in days:
            TimeSlot.objects.create(
                day_of_week=day, start_time="09:00", end_time="12:00"
            )
            TimeSlot.objects.create(
                day_of_week=day, start_time="14:00", end_time="18:00"
            )
        logger.info("timeslots_seeded", count=TimeSlot.objects.count())

    def _create_breeds_and_categories(self):
        Breed.objects.all().delete()
        Category.objects.all().delete()
        Brand.objects.all().delete()

        BreedFactory.create_batch(5, species="DOG")
        BreedFactory.create_batch(5, species="CAT")

        CategoryFactory(name="Alimentação")
        CategoryFactory(name="Higiene")
        CategoryFactory(name="Brinquedos")
        CategoryFactory(name="Farmácia")
        BrandFactory(name="PetFood Inc.")
        BrandFactory(name="CleanPet")
        BrandFactory(name="ToyFun")

    def _create_services(self):
        Service.objects.all().delete()
        services_data = [
            {"name": "Banho", "price": 50.00, "duration_minutes": 45},
            {"name": "Tosa Higiênica", "price": 35.00, "duration_minutes": 30},
            {"name": "Consulta Veterinária", "price": 120.00, "duration_minutes": 60},
            {"name": "Aplicação de Vacina", "price": 80.00, "duration_minutes": 15},
        ]
        services = [Service.objects.create(**data) for data in services_data]
        logger.info("services_seeded", count=len(services))
        return services

    def _create_products(self):
        Product.objects.all().delete()
        products_data = [
            {
                "name": "Ração Premium para Cães Adultos 15kg",
                "category": "Alimentação",
                "brand": "PetFood Inc.",
                "price": "250.00",
            },
            {
                "name": "Ração Gatos Castrados Salmão 3kg",
                "category": "Alimentação",
                "brand": "PetFood Inc.",
                "price": "95.00",
            },
            {
                "name": "Shampoo Antipulgas e Carrapatos 500ml",
                "category": "Higiene",
                "brand": "CleanPet",
                "price": "45.00",
            },
            {
                "name": "Tapete Higiênico Super Absorvente 30un",
                "category": "Higiene",
                "brand": "CleanPet",
                "price": "60.00",
            },
            {
                "name": "Bolinha de Borracha Resistente",
                "category": "Brinquedos",
                "brand": "ToyFun",
                "price": "25.00",
            },
            {
                "name": "Arranhador de Sisal para Gatos",
                "category": "Brinquedos",
                "brand": "ToyFun",
                "price": "80.00",
            },
            {
                "name": "Antipulgas de Pipeta para Cães (10 a 25kg)",
                "category": "Farmácia",
                "brand": "CleanPet",
                "price": "55.00",
            },
        ]
        products = []
        for data in products_data:
            data["category"] = Category.objects.get(name=data["category"])
            data["brand"] = Brand.objects.get(name=data["brand"])
            data["price"] = Decimal(data["price"])
            products.append(ProductFactory(**data))
        logger.info("products_seeded", count=len(products))
        return products

    def _create_lots(self, products):
        ProductLot.objects.all().delete()
        today = timezone.now().date()
        for i, product in enumerate(products):
            ProductLot.objects.create(
                product=product,
                lot_number=f"LOTE-{today.year}-{i + 1:03d}",
                quantity=random.randint(15, 50),
                expiration_date=today + timedelta(days=random.randint(60, 400)),
            )
        ProductLot.objects.create(
            product=products[0],
            lot_number=f"PROMO-{today.year}-001",
            quantity=10,
            expiration_date=today + timedelta(days=25),
        )
        logger.info("product_lots_seeded", count=ProductLot.objects.count())

    def _create_customers(self):
        User.objects.filter(is_superuser=False, is_staff=False).delete()
        customers = CustomerFactory.create_batch(7)
        logger.info("customers_seeded", count=len(customers))
        return customers

    def _create_pets(self, customers):
        Pet.objects.all().delete()
        dog_breeds = list(Breed.objects.filter(species="DOG"))
        cat_breeds = list(Breed.objects.filter(species="CAT"))
        pets = []
        for customer in customers:
            num_pets = random.randint(1, 2)
            for _ in range(num_pets):
                breed = random.choice(
                    dog_breeds if random.random() > 0.3 else cat_breeds
                )
                pets.append(PetFactory(owner=customer, breed=breed))
        logger.info("pets_seeded", count=len(pets))
        return pets

    def _create_health_records(self, pets):
        for pet in pets:
            if random.random() > 0.5:
                HealthRecordFactory(pet=pet)

    def _create_appointments(self, pets, services):
        Appointment.objects.all().delete()
        today = timezone.now()
        for i in range(len(pets)):
            if random.random() > 0.4:
                pet = random.choice(pets)
                service = random.choice(services)
                future_time = today.replace(
                    hour=random.randint(9, 17), minute=random.choice([0, 15, 30, 45])
                ) + timedelta(days=i + 1)
                AppointmentFactory(pet=pet, service=service, schedule_time=future_time)
        logger.info("appointments_seeded", count=Appointment.objects.count())

    def _create_sales(self):
        Sale.objects.all().delete()
        staff_user, created = User.objects.get_or_create(
            username="staff_seeder",
            defaults={
                "is_staff": True,
                "first_name": "Staff",
                "email": "staff@seeder.com",
            },
        )
        if created:
            staff_user.set_password("seedpassword")
            staff_user.save()

        customers = list(Customer.objects.all())
        lots_with_stock = list(ProductLot.objects.filter(quantity__gt=5))
        if not lots_with_stock:
            return

        for _ in range(7):
            customer = random.choice(customers)
            num_items = random.randint(1, 3)
            items_to_sell = random.sample(
                lots_with_stock, min(num_items, len(lots_with_stock))
            )
            items_data = [
                {"lot": lot, "quantity": random.randint(1, 2)} for lot in items_to_sell
            ]

            if items_data:
                SaleService.create_sale(
                    user=staff_user, customer=customer, items_data=items_data
                )

        logger.info("sales_seeded", count=Sale.objects.count())
