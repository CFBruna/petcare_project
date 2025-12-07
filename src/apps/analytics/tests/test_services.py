from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from src.apps.accounts.factories import CustomerFactory
from src.apps.analytics.services import AnalyticsService
from src.apps.pets.factories import PetFactory
from src.apps.schedule.factories import AppointmentFactory, ServiceFactory
from src.apps.schedule.models import Appointment
from src.apps.store.factories import ProductLotFactory, SaleFactory, SaleItemFactory


@pytest.mark.django_db
class TestAnalyticsService:
    """Test suite for AnalyticsService dashboard metrics."""

    def test_get_dashboard_metrics_returns_correct_structure(self):
        """
        Test that dashboard metrics returns all required fields.
        """
        data = AnalyticsService.get_dashboard_metrics(days=7)

        assert "period_start" in data
        assert "period_end" in data
        assert "metrics_history" in data
        assert "status_distribution" in data
        assert "top_products" in data

    def test_metrics_history_has_all_days(self):
        """
        Test that metrics_history includes all days in the period.
        Even days with no data should be present with zero values.
        """
        days = 7
        data = AnalyticsService.get_dashboard_metrics(days=days)

        assert len(data["metrics_history"]) == days

        # Verify each day has required fields
        for metric in data["metrics_history"]:
            assert "date" in metric
            assert "total_revenue" in metric
            assert "total_appointments" in metric
            assert "new_customers" in metric

    def test_metrics_aggregation_with_sales_data(self):
        """
        Test that revenue is correctly aggregated from sales.
        """
        # Create sales for today
        customer = CustomerFactory()
        lot = ProductLotFactory(quantity=100)

        sale1 = SaleFactory(customer=customer, total_value=Decimal("100.00"))
        sale2 = SaleFactory(customer=customer, total_value=Decimal("150.00"))

        SaleItemFactory(sale=sale1, lot=lot, quantity=1, unit_price=Decimal("100.00"))
        SaleItemFactory(sale=sale2, lot=lot, quantity=1, unit_price=Decimal("150.00"))

        data = AnalyticsService.get_dashboard_metrics(days=1)

        # Today's metrics should include both sales
        today_metrics = data["metrics_history"][0]
        assert today_metrics["total_revenue"] == 250.00  # 100 + 150

    def test_status_distribution_counts_appointments(self):
        """
        Test that status distribution correctly counts appointments by status.
        """
        pet = PetFactory()
        service = ServiceFactory()

        # Create appointments with different statuses
        AppointmentFactory(
            pet=pet, service=service, status=Appointment.Status.CONFIRMED
        )
        AppointmentFactory(
            pet=pet, service=service, status=Appointment.Status.CONFIRMED
        )
        AppointmentFactory(pet=pet, service=service, status=Appointment.Status.PENDING)

        data = AnalyticsService.get_dashboard_metrics(days=1)

        status_dict = {
            item["status"]: item["count"] for item in data["status_distribution"]
        }

        assert status_dict.get(Appointment.Status.CONFIRMED, 0) == 2
        assert status_dict.get(Appointment.Status.PENDING, 0) == 1

    def test_top_products_ordered_by_revenue(self):
        """
        Test that top products are ordered by revenue (highest first).
        """
        customer = CustomerFactory()
        lot1 = ProductLotFactory(quantity=100)
        lot2 = ProductLotFactory(quantity=100)

        sale = SaleFactory(customer=customer)

        # Product 1: 2 units at $100 = $200
        SaleItemFactory(sale=sale, lot=lot1, quantity=2, unit_price=Decimal("100.00"))

        # Product 2: 5 units at $50 = $250 (should be first)
        SaleItemFactory(sale=sale, lot=lot2, quantity=5, unit_price=Decimal("50.00"))

        data = AnalyticsService.get_dashboard_metrics(days=1)

        top_products = data["top_products"]
        assert len(top_products) > 0

        # First product should have highest revenue
        assert float(top_products[0]["revenue_generated"]) == 250.00

    def test_new_customers_count(self):
        """
        Test that new customers are correctly counted per day.
        """
        # Create customers with different join dates
        today = timezone.now()
        yesterday = today - timedelta(days=1)

        user1 = User.objects.create_user(username="test1", email="test1@test.com")
        user1.date_joined = today
        user1.save()
        CustomerFactory(user=user1)

        user2 = User.objects.create_user(username="test2", email="test2@test.com")
        user2.date_joined = yesterday
        user2.save()
        CustomerFactory(user=user2)

        data = AnalyticsService.get_dashboard_metrics(days=2)

        # Today should have 1 new customer
        today_metrics = data["metrics_history"][-1]  # Last day is today
        assert today_metrics["new_customers"] == 1

    def test_different_day_ranges(self):
        """
        Test that service works with different day ranges.
        """
        for days in [1, 7, 30]:
            data = AnalyticsService.get_dashboard_metrics(days=days)
            assert len(data["metrics_history"]) == days

    def test_empty_database_returns_zero_values(self):
        """
        Test that service handles empty database gracefully.
        """
        data = AnalyticsService.get_dashboard_metrics(days=7)

        # Should still return structure with zeros
        assert len(data["metrics_history"]) == 7
        assert data["status_distribution"] == []
        assert data["top_products"] == []

        for metric in data["metrics_history"]:
            assert metric["total_revenue"] == 0.0
            assert metric["total_appointments"] == 0
            assert metric["new_customers"] == 0
