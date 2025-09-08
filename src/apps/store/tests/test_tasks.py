from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import connection
from django.utils import timezone

from src.apps.store.tasks import (
    apply_expiration_discounts,
    generate_daily_promotions_report,
    generate_daily_sales_report,
)

from .factories import (
    ProductFactory,
    ProductLotFactory,
    SaleFactory,
    SaleItemFactory,
)


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


@pytest.mark.django_db
class TestStoreReportTasks:
    def test_generate_daily_sales_report_with_data(self, mocker):
        mocked_now = timezone.make_aware(timezone.datetime(2025, 8, 26, 10, 0))
        mocker.patch("django.utils.timezone.localdate", return_value=mocked_now.date())
        send_mail_mock = mocker.patch("src.apps.store.tasks.send_mail")

        yesterday = mocked_now.date() - timedelta(days=1)
        product = ProductFactory(price=Decimal("100.00"))
        lot = ProductLotFactory(product=product)

        sale = SaleFactory(total_value=Decimal("200.00"))
        sale.created_at = mocked_now - timedelta(days=1)
        sale.save()
        SaleItemFactory(sale=sale, lot=lot, quantity=2, unit_price=Decimal("100.00"))

        result = generate_daily_sales_report()

        send_mail_mock.assert_called_once()
        subject = send_mail_mock.call_args[0][0]
        message = send_mail_mock.call_args[0][1]

        assert (
            f"Relatório Diário de Vendas - {yesterday.strftime('%d/%m/%Y')}" in subject
        )
        assert product.name in message
        assert "enviado com sucesso" in result

    def test_generate_daily_sales_report_no_data(self, mocker):
        mocked_now = timezone.make_aware(timezone.datetime(2025, 8, 26, 10, 0))
        mocker.patch("django.utils.timezone.localdate", return_value=mocked_now.date())
        send_mail_mock = mocker.patch("src.apps.store.tasks.send_mail")

        generate_daily_sales_report()

        send_mail_mock.assert_called_once()
        message = send_mail_mock.call_args[0][1]
        assert "Nenhuma venda foi registrada nesta data." in message

    def test_promotion_report_detects_newly_promoted_and_unpromoted(self, mocker):
        mocked_now = timezone.make_aware(timezone.datetime(2025, 8, 26, 10, 0))
        yesterday_str = (mocked_now - timedelta(days=1)).isoformat()
        mocker.patch("django.utils.timezone.localdate", return_value=mocked_now.date())
        send_mail_mock = mocker.patch("src.apps.store.tasks.send_mail")

        with connection.cursor() as cursor:
            newly_promoted = ProductLotFactory(
                auto_discount_percentage=Decimal("10.00")
            )
            cursor.execute(
                "UPDATE store_productlot SET updated_at = %s WHERE id = %s",
                [yesterday_str, newly_promoted.id],
            )
            newly_unpromoted = ProductLotFactory(
                auto_discount_percentage=Decimal("0.00")
            )
            cursor.execute(
                "UPDATE store_productlot SET updated_at = %s WHERE id = %s",
                [yesterday_str, newly_unpromoted.id],
            )

        generate_daily_promotions_report()

        send_mail_mock.assert_called_once()
        message = send_mail_mock.call_args[0][1]

        assert "Produtos que ENTRARAM em promoção" in message
        assert newly_promoted.product.name in message
        assert "Produtos que SAÍRAM de promoção" in message
        assert newly_unpromoted.product.name in message
