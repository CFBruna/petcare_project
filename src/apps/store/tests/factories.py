from datetime import timedelta

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from faker import Faker

from src.apps.store.models import (
    Brand,
    Category,
    Product,
    ProductLot,
    Promotion,
    PromotionRule,
    Sale,
    SaleItem,
)

fake = Faker("pt_BR")


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ("name",)

    name = factory.Iterator(
        ["Ração", "Brinquedos", "Higiene", "Acessórios", "Farmácia"]
    )
    description = factory.LazyFunction(fake.sentence)


class BrandFactory(DjangoModelFactory):
    class Meta:
        model = Brand
        django_get_or_create = ("name",)

    name = factory.Iterator(["Royal Canin", "Pedigree", "Whiskas", "PetSafe", "Kong"])


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.LazyFunction(lambda: " ".join(fake.words(nb=3)).title())
    sku = factory.LazyFunction(lambda: fake.ean(8))
    barcode = factory.LazyFunction(lambda: fake.ean(13))
    brand = factory.SubFactory(BrandFactory)
    category = factory.SubFactory(CategoryFactory)
    description = factory.LazyFunction(fake.paragraph)
    price = factory.Faker(
        "pydecimal",
        left_digits=3,
        right_digits=2,
        positive=True,
        min_value=10,
        max_value=300,
    )


class ProductLotFactory(DjangoModelFactory):
    class Meta:
        model = ProductLot

    product = factory.SubFactory(ProductFactory)
    lot_number = factory.LazyFunction(lambda: fake.bothify(text="???-#####").upper())
    quantity = factory.Faker("random_int", min=10, max=100)
    expiration_date = factory.Faker("future_date", end_date="+2y")


class PromotionFactory(DjangoModelFactory):
    class Meta:
        model = Promotion

    name = factory.Sequence(lambda n: f"Promoção {n}: {fake.catch_phrase()}")
    start_date = factory.LazyFunction(timezone.now)
    end_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=30))


class PromotionRuleFactory(DjangoModelFactory):
    class Meta:
        model = PromotionRule

    promotion = factory.SubFactory(PromotionFactory)
    lot = factory.SubFactory(ProductLotFactory)
    discount_percentage = factory.Faker(
        "pydecimal", left_digits=2, right_digits=2, min_value=5, max_value=50
    )
    promotional_stock = 10


class SaleFactory(DjangoModelFactory):
    class Meta:
        model = Sale

    customer = factory.SubFactory("src.apps.accounts.tests.factories.CustomerFactory")
    processed_by = factory.SubFactory("src.apps.accounts.tests.factories.UserFactory")


class SaleItemFactory(DjangoModelFactory):
    class Meta:
        model = SaleItem

    sale = factory.SubFactory(SaleFactory)
    lot = factory.SubFactory(ProductLotFactory)
    quantity = factory.Faker("random_int", min=1, max=5)
    unit_price = factory.LazyAttribute(lambda o: o.lot.final_price)
