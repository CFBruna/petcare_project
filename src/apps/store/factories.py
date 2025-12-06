import random
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

REALISTIC_PRODUCT_NAMES = [
    "Ração Premium para Cães Adultos 15kg",
    "Ração Filhotes Raças Pequenas 3kg",
    "Ração Gatos Castrados Salmão 10kg",
    "Ração Especial para Filhotes 7.5kg",
    "Ração Super Premium Frango e Arroz 20kg",
    "Ração Hipoalergênica para Cães Sensíveis 12kg",
    "Ração Gatos Adultos Mix de Peixes 8kg",
    "Petisco Natural de Frango Desidratado 200g",
    "Osso de Couro Bovino para Cães",
    "Bifinho de Carne Bovina 500g",
    "Snack Dental para Cães Adultos",
    "Petisco Freeze Dried de Salmão para Gatos 50g",
    "Shampoo Antipulgas e Carrapatos 500ml",
    "Condicionador Hidratante para Pelos Longos 500ml",
    "Tapete Higiênico Super Absorvente 30un",
    "Lenços Umedecidos Pet Fresh 100un",
    "Escova de Dentes Pet com Cerdas Macias",
    "Perfume Colônia Pet Lavanda 120ml",
    "Lixa para Unhas de Gatos",
    "Bolinha de Borracha Resistente Grande",
    "Corda de Algodão Trançada para Cães",
    "Arranhador de Sisal com Bolinha Suspensa",
    "Pelúcia Mordedor com Som",
    "Bola Dispenser de Petiscos",
    "Varinha com Penas para Gatos",
    "Frisbee Flutuante para Cães",
    "Coleira Ajustável Nylon Refletiva P/M/G",
    "Guia Retrátil Automática 5 metros",
    "Cama Ortopédica Cinza com Memory Foam",
    "Comedouro Duplo Inox Antiaderente",
    "Bebedouro Fonte Automática 3 Litros",
    "Caixa de Transporte Tamanho M Resistente",
    "Peitoral Anti-Puxão Ajustável",
    "Antipulgas Spot On para Cães 10-25kg",
    "Vermífugo Comprimido Sabor Carne 4 doses",
    "Suplemento Vitamínico para Articulações",
    "Pomada Cicatrizante Veterinária 30g",
    "Colírio Oftálmico Lubrificante 10ml",
    "Sabonete Antisséptico para Pets 90g",
    "Anti-inflamatório Natural para Cães",
    "Areia Higiênica Perfumada para Gatos 4kg",
    "Granulado Sanitário Biodegradável 6kg",
    "Bandeja Sanitária Fechada com Filtro",
]


class CategoryFactory(DjangoModelFactory):
    """Factory for Category model with realistic pet shop categories."""

    class Meta:
        model = Category
        django_get_or_create = ("name",)

    name = factory.Iterator(
        ["Ração", "Brinquedos", "Higiene", "Acessórios", "Farmácia", "Petiscos"]
    )
    description = factory.LazyFunction(fake.sentence)


class BrandFactory(DjangoModelFactory):
    """Factory for Brand model with realistic pet brands."""

    class Meta:
        model = Brand
        django_get_or_create = ("name",)

    name = factory.Iterator(
        [
            "Royal Canin",
            "Pedigree",
            "Whiskas",
            "PetSafe",
            "Kong",
            "Premier Pet",
            "Golden",
            "Nestlé Purina",
            "Equilíbrio",
            "N&D Natural & Delicious",
            "Faro & Focinhos",
        ]
    )


class ProductFactory(DjangoModelFactory):
    """Factory for Product model with realistic pet shop product names."""

    class Meta:
        model = Product

    name = factory.LazyFunction(lambda: random.choice(REALISTIC_PRODUCT_NAMES))
    sku = factory.LazyFunction(lambda: fake.ean8())
    barcode = factory.LazyFunction(lambda: fake.ean13())
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
    """Factory for ProductLot model."""

    class Meta:
        model = ProductLot

    product = factory.SubFactory(ProductFactory)
    lot_number = factory.LazyFunction(lambda: fake.bothify(text="???-####").upper())
    quantity = factory.Faker("random_int", min=10, max=100)
    expiration_date = factory.Faker("future_date", end_date="+2y")


class PromotionFactory(DjangoModelFactory):
    """Factory for Promotion model."""

    class Meta:
        model = Promotion

    name = factory.Sequence(lambda n: f"Promoção {n} - {fake.catch_phrase()}")
    start_date = factory.LazyFunction(timezone.now)
    end_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=30))


class PromotionRuleFactory(DjangoModelFactory):
    """Factory for PromotionRule model."""

    class Meta:
        model = PromotionRule

    promotion = factory.SubFactory(PromotionFactory)
    lot = factory.SubFactory(ProductLotFactory)
    discount_percentage = factory.Faker(
        "pydecimal", left_digits=2, right_digits=2, min_value=5, max_value=50
    )
    promotional_stock = 10


class SaleFactory(DjangoModelFactory):
    """Factory for Sale model."""

    class Meta:
        model = Sale

    customer = factory.SubFactory("src.apps.accounts.factories.CustomerFactory")
    processed_by = factory.SubFactory("src.apps.accounts.factories.UserFactory")


class SaleItemFactory(DjangoModelFactory):
    """Factory for SaleItem model."""

    class Meta:
        model = SaleItem

    sale = factory.SubFactory(SaleFactory)
    lot = factory.SubFactory(ProductLotFactory)
    quantity = factory.Faker("random_int", min=1, max=5)
    unit_price = factory.LazyAttribute(lambda o: o.lot.final_price)
