from datetime import time, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

from src.apps.pets.tests.factories import PetFactory
from src.apps.schedule.models import Appointment, TimeSlot
from src.apps.schedule.tests.factories import ServiceFactory
from src.apps.store.tasks import (
    apply_expiration_discounts,
    generate_daily_promotions_report,
    generate_daily_sales_report,
    simulate_daily_activity,
)

from .factories import (
    ProductFactory,
    ProductLotFactory,
    PromotionFactory,
    SaleFactory,
    SaleItemFactory,
)


@pytest.mark.django_db
class TestExpirationDiscountTask:
    def test_apply_expiration_discounts_correctly(self):
        today = timezone.now().date()
        lot_no_discount = ProductLotFactory(expiration_date=today + timedelta(days=31))
        lot_10_percent = ProductLotFactory(expiration_date=today + timedelta(days=30))
        lot_20_percent = ProductLotFactory(expiration_date=today + timedelta(days=15))
        lot_30_percent = ProductLotFactory(expiration_date=today + timedelta(days=7))
        lot_expired = ProductLotFactory(expiration_date=today - timedelta(days=1))
        lot_no_expiration = ProductLotFactory(expiration_date=None)

        result = apply_expiration_discounts()

        lot_no_discount.refresh_from_db()
        lot_10_percent.refresh_from_db()
        lot_20_percent.refresh_from_db()
        lot_30_percent.refresh_from_db()
        lot_expired.refresh_from_db()
        lot_no_expiration.refresh_from_db()

        assert lot_no_discount.auto_discount_percentage == Decimal("0")
        assert lot_10_percent.auto_discount_percentage == Decimal("10")
        assert lot_20_percent.auto_discount_percentage == Decimal("20")
        assert lot_30_percent.auto_discount_percentage == Decimal("30")
        assert lot_expired.auto_discount_percentage == Decimal("0")
        assert lot_no_expiration.auto_discount_percentage == Decimal("0")

        assert "3 lotes tiveram seu desconto por validade atualizado." in result


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
        assert "Faturamento Total do Dia" in message
        assert "enviado com sucesso" in result

    def test_generate_daily_sales_report_no_data(self, mocker):
        mocked_now = timezone.make_aware(timezone.datetime(2025, 8, 26, 10, 0))
        mocker.patch("django.utils.timezone.localdate", return_value=mocked_now.date())
        send_mail_mock = mocker.patch("src.apps.store.tasks.send_mail")

        generate_daily_sales_report()

        send_mail_mock.assert_called_once()
        message = send_mail_mock.call_args[0][1]
        assert "Nenhuma venda foi realizada nesta data." in message

    def test_promotion_report_detects_newly_promoted_and_unpromoted(self, mocker):
        mocked_now = timezone.make_aware(timezone.datetime(2025, 8, 26, 10, 0))
        mocker.patch("django.utils.timezone.localdate", return_value=mocked_now.date())
        send_mail_mock = mocker.patch("src.apps.store.tasks.send_mail")

        # Arrange
        start_date_aware = mocked_now - timedelta(days=2)
        end_date_aware = mocked_now - timedelta(days=1)
        PromotionFactory(
            start_date=start_date_aware,
            end_date=end_date_aware,
        )

        generate_daily_promotions_report()

        send_mail_mock.assert_called_once()
        message = send_mail_mock.call_args[0][1]

        assert "Relatório de promoções ativas" in message


@pytest.mark.django_db
class TestSimulateDailyActivityTask:
    @patch("src.apps.store.tasks.apply_expiration_discounts.delay")
    def test_simulation_creates_at_least_two_confirmed_appointments_for_today(
        self, mock_apply_discounts
    ):
        # Arrange
        today = timezone.now().date()
        PetFactory.create_batch(5)
        ServiceFactory.create_batch(3)

        for day in range(7):
            TimeSlot.objects.get_or_create(
                day_of_week=day,
                start_time=time(8, 0),
                defaults={"end_time": time(20, 0)},
            )

        # Act
        result = simulate_daily_activity.s(num_appointments=7).apply()

        # Assert
        assert result.successful()
        assert "appointments" in result.result

        appointments_today = Appointment.objects.filter(schedule_time__date=today)
        assert appointments_today.exists()

        confirmed_today = appointments_today.filter(status=Appointment.Status.CONFIRMED)
        assert confirmed_today.count() >= 2

        mock_apply_discounts.assert_called_once()
