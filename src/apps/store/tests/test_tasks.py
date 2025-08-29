from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from src.apps.store.models import ProductLot, Promotion
from src.apps.store.tasks import (
    apply_expiration_discounts,
    generate_daily_promotions_report,
    generate_daily_sales_report,
)

from .factories import (
    ProductFactory,
    ProductLotFactory,
    PromotionFactory,
    PromotionRuleFactory,
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
        # Arrange
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

        SaleFactory(total_value=Decimal("50.00"))

        # Act
        result = generate_daily_sales_report()

        # Assert
        send_mail_mock.assert_called_once()
        call_args = send_mail_mock.call_args[0]
        subject = call_args[0]
        message = call_args[1]

        assert (
            f"Relatório Diário de Vendas - {yesterday.strftime('%d/%m/%Y')}" in subject
        )
        assert "(1 vendas)" in subject
        assert f"Venda #{sale.id}" in message
        assert product.name in message
        assert "Faturamento Total do Dia: R$ 200.00" in message
        assert "enviado com sucesso" in result

    def test_generate_daily_sales_report_no_data(self, mocker):
        # Arrange
        mocked_now = timezone.make_aware(timezone.datetime(2025, 8, 26, 10, 0))
        mocker.patch("django.utils.timezone.localdate", return_value=mocked_now.date())
        send_mail_mock = mocker.patch("src.apps.store.tasks.send_mail")

        # Act
        generate_daily_sales_report()

        # Assert
        send_mail_mock.assert_called_once()
        message = send_mail_mock.call_args[0][1]
        assert "Nenhuma venda foi registrada nesta data." in message

    def test_generate_daily_promotions_report(self, mocker):
        # Arrange
        mocked_now = timezone.make_aware(timezone.datetime(2025, 8, 26, 10, 0))
        mocker.patch("django.utils.timezone.localdate", return_value=mocked_now.date())
        send_mail_mock = mocker.patch("src.apps.store.tasks.send_mail")

        manual_promo = PromotionFactory(
            start_date=mocked_now - timedelta(days=5),
            end_date=mocked_now + timedelta(days=5),
        )
        rule = PromotionRuleFactory(promotion=manual_promo)
        manual_promo_product_name = rule.lot.product.name

        auto_promo_lot = ProductLotFactory(auto_discount_percentage=Decimal("20.00"))
        auto_promo_product_name = auto_promo_lot.product.name

        # Act
        result = generate_daily_promotions_report()

        # Assert
        send_mail_mock.assert_called_once()
        call_args = send_mail_mock.call_args[0]
        subject = call_args[0]
        message = call_args[1]

        assert "Relatório Diário de Promoções" in subject
        assert manual_promo.name in message
        assert manual_promo_product_name in message
        assert auto_promo_product_name in message
        assert "enviado com sucesso" in result

    def test_generate_daily_promotions_report_no_data(self, mocker):
        # Arrange
        mocked_now = timezone.make_aware(timezone.datetime(2025, 8, 26, 10, 0))
        mocker.patch("django.utils.timezone.localdate", return_value=mocked_now.date())
        send_mail_mock = mocker.patch("src.apps.store.tasks.send_mail")

        Promotion.objects.all().delete()
        ProductLot.objects.update(auto_discount_percentage=0)

        # Act
        generate_daily_promotions_report()

        # Assert
        send_mail_mock.assert_called_once()
        call_args = send_mail_mock.call_args[0]
        message = call_args[1]

        assert "Nenhuma promoção manual ativa hoje." in message
        assert "Nenhuma promoção automática ativa hoje." in message
