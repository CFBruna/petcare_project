import pytest
from django.forms import inlineformset_factory

from src.apps.store.forms import SaleItemFormSet
from src.apps.store.models import Sale, SaleItem

from .factories import ProductFactory, SaleFactory


@pytest.mark.django_db
class TestSaleItemFormSet:
    def setup_method(self):
        self.SaleItemFormSet = inlineformset_factory(
            Sale,
            SaleItem,
            formset=SaleItemFormSet,
            fields=("product", "quantity"),
            extra=2,
        )

    def test_formset_is_valid_with_sufficient_stock(self):
        product = ProductFactory(stock=10)
        sale = SaleFactory()
        formset_data = {
            "items-TOTAL_FORMS": "1",
            "items-INITIAL_FORMS": "0",
            "items-0-product": product.id,
            "items-0-quantity": 5,
        }
        formset = self.SaleItemFormSet(formset_data, instance=sale, prefix="items")
        assert formset.is_valid(), formset.errors

    def test_formset_is_invalid_with_insufficient_stock(self):
        product = ProductFactory(stock=5)
        sale = SaleFactory()
        formset_data = {
            "items-TOTAL_FORMS": "1",
            "items-INITIAL_FORMS": "0",
            "items-0-product": product.id,
            "items-0-quantity": 10,
        }
        formset = self.SaleItemFormSet(formset_data, instance=sale, prefix="items")
        assert not formset.is_valid()
        assert "Estoque insuficiente" in str(formset.non_form_errors())

    def test_formset_is_invalid_if_total_quantity_exceeds_stock(self):
        product = ProductFactory(stock=10)
        sale = SaleFactory()
        formset_data = {
            "items-TOTAL_FORMS": "2",
            "items-INITIAL_FORMS": "0",
            "items-0-product": product.id,
            "items-0-quantity": 8,
            "items-1-product": product.id,
            "items-1-quantity": 7,
        }
        formset = self.SaleItemFormSet(formset_data, instance=sale, prefix="items")
        assert not formset.is_valid()
        assert "Disponível: 10, Solicitado: 15" in str(formset.non_form_errors())
