import factory
from factory.django import DjangoModelFactory

from src.apps.store.models import Brand, Category, Product, Sale, SaleItem


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Categoria {n}")


class BrandFactory(DjangoModelFactory):
    class Meta:
        model = Brand

    name = factory.Sequence(lambda n: f"Marca {n}")


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Produto {n}")
    brand = factory.SubFactory(BrandFactory)
    category = factory.SubFactory(CategoryFactory)
    price = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    stock = 10


class SaleFactory(DjangoModelFactory):
    class Meta:
        model = Sale

    customer = factory.SubFactory("src.apps.accounts.tests.factories.CustomerFactory")
    processed_by = factory.SubFactory("src.apps.accounts.tests.factories.UserFactory")


class SaleItemFactory(DjangoModelFactory):
    class Meta:
        model = SaleItem

    sale = factory.SubFactory(SaleFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker("random_int", min=1, max=5)
    unit_price = factory.LazyAttribute(lambda o: o.product.price)
