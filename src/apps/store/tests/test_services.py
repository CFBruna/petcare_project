from decimal import Decimal

import pytest
from django.utils import timezone

from src.apps.accounts.tests.factories import UserFactory
from src.apps.store.models import Sale
from src.apps.store.services import (
    InsufficientStockError,
    calculate_product_final_price,
    create_sale,
)
from src.apps.store.tests.factories import (
    ProductFactory,
    ProductLotFactory,
    PromotionFactory,
    PromotionRuleFactory,
)


@pytest.mark.django_db
class TestStoreServices:
    def test_create_sale_successfully(self):
        user = UserFactory()
        lot1 = ProductLotFactory(quantity=10, product__price=Decimal("20.00"))
        lot2 = ProductLotFactory(quantity=5, product__price=Decimal("10.00"))

        items_data = [
            {"lot": lot1, "quantity": 3},
            {"lot": lot2, "quantity": 2},
        ]

        sale = create_sale(user=user, items_data=items_data)

        lot1.refresh_from_db()
        lot2.refresh_from_db()

        assert Sale.objects.count() == 1
        assert sale.items.count() == 2
        assert sale.total_value == Decimal("80.00")
        assert lot1.quantity == 7
        assert lot2.quantity == 3

    def test_create_sale_insufficient_stock_fails(self):
        user = UserFactory()
        lot = ProductLotFactory(quantity=5)
        items_data = [{"lot": lot, "quantity": 10}]

        with pytest.raises(InsufficientStockError):
            create_sale(user=user, items_data=items_data)

        assert Sale.objects.count() == 0
        lot.refresh_from_db()
        assert lot.quantity == 5

    def test_calculate_final_price_reflects_active_promotion(self):
        product = ProductFactory(price=Decimal("100.00"))
        lot = ProductLotFactory(product=product, quantity=10)
        now = timezone.now()
        promotion = PromotionFactory(
            start_date=now - timezone.timedelta(days=1),
            end_date=now + timezone.timedelta(days=1),
        )
        PromotionRuleFactory(
            promotion=promotion,
            lot=lot,
            discount_percentage=Decimal("20.00"),
        )

        final_price = calculate_product_final_price(product)
        assert final_price == Decimal("80.00")

    def test_create_sale_logs_error_on_insufficient_stock(self, caplog):
        # Arrange
        user = UserFactory()
        lot = ProductLotFactory(quantity=2)
        items_data = [{"lot": lot, "quantity": 5}]

        # Act
        with pytest.raises(InsufficientStockError):
            create_sale(user=user, items_data=items_data)

        # Assert
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "ERROR"
        assert "Sale creation failed" in record.message
        assert "Estoque insuficiente" in record.message
        assert "Disponível: 2, Solicitado: 5" in record.message
