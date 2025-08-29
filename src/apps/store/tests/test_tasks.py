from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from src.apps.store.tasks import apply_expiration_discounts

from .factories import ProductLotFactory


@pytest.mark.django_db
class TestExpirationDiscountTask:
    def test_apply_expiration_discounts_correctly(self):
        today = timezone.now().date()

        lot_no_discount = ProductLotFactory(expiration_date=today + timedelta(days=100))
        lot_10_percent = ProductLotFactory(expiration_date=today + timedelta(days=90))
        lot_20_percent = ProductLotFactory(expiration_date=today + timedelta(days=60))
        lot_30_percent = ProductLotFactory(expiration_date=today + timedelta(days=30))
        lot_50_percent = ProductLotFactory(expiration_date=today + timedelta(days=14))
        lot_60_percent = ProductLotFactory(expiration_date=today + timedelta(days=5))
        lot_expired = ProductLotFactory(expiration_date=today - timedelta(days=1))
        lot_no_expiration = ProductLotFactory(expiration_date=None)

        result = apply_expiration_discounts()

        lot_no_discount.refresh_from_db()
        lot_10_percent.refresh_from_db()
        lot_20_percent.refresh_from_db()
        lot_30_percent.refresh_from_db()
        lot_50_percent.refresh_from_db()
        lot_60_percent.refresh_from_db()
        lot_expired.refresh_from_db()
        lot_no_expiration.refresh_from_db()

        assert lot_no_discount.auto_discount_percentage == Decimal("0")
        assert lot_10_percent.auto_discount_percentage == Decimal("10")
        assert lot_20_percent.auto_discount_percentage == Decimal("20")
        assert lot_30_percent.auto_discount_percentage == Decimal("30")
        assert lot_50_percent.auto_discount_percentage == Decimal("50")
        assert lot_60_percent.auto_discount_percentage == Decimal("60")
        assert lot_expired.auto_discount_percentage == Decimal("0")
        assert lot_no_expiration.auto_discount_percentage == Decimal("0")

        assert "5 lotes tiveram seu desconto por validade atualizado." in result
