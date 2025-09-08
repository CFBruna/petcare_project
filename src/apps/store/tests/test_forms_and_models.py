import pytest
from django.utils import timezone

from src.apps.store.forms import BrandAdminForm, CategoryAdminForm
from src.apps.store.models import Product

from .factories import (
    ProductFactory,
    ProductLotFactory,
    PromotionFactory,
    PromotionRuleFactory,
)


@pytest.mark.django_db
class TestStoreForms:
    def test_category_form_clean_name_empty(self):
        form = CategoryAdminForm(data={"name": ""})
        assert not form.is_valid()

    def test_brand_form_clean_name_empty(self):
        form = BrandAdminForm(data={"name": ""})
        assert not form.is_valid()


@pytest.mark.django_db
class TestStoreModelsExtra:
    def test_promotion_rule_str(self):
        rule = PromotionRuleFactory(lot__lot_number="LOTE123")
        assert "LOTE123" in str(rule)

    def test_product_queryset_on_promotion(self):
        now = timezone.now()

        promo_prod = ProductFactory()
        promo_lot = ProductLotFactory(product=promo_prod)
        promotion = PromotionFactory(
            start_date=now - timezone.timedelta(days=1),
            end_date=now + timezone.timedelta(days=1),
        )
        PromotionRuleFactory(promotion=promotion, lot=promo_lot)

        auto_promo_prod = ProductFactory()
        ProductLotFactory(product=auto_promo_prod, auto_discount_percentage=20)

        no_promo_prod = ProductFactory()
        ProductLotFactory(product=no_promo_prod)

        promotional_products = Product.objects.on_promotion()
        assert promo_prod in promotional_products
        assert auto_promo_prod in promotional_products
        assert no_promo_prod not in promotional_products
