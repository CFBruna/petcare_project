from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from src.apps.accounts.factories import CustomerFactory, UserFactory
from src.apps.store.factories import ProductLotFactory, SaleFactory, SaleItemFactory


@pytest.mark.django_db
class TestDashboardMetricsAPI:
    """Test suite for /api/v1/analytics/dashboard/ endpoint."""

    @pytest.fixture
    def authenticated_client(self):
        """Create an authenticated API client."""
        user = UserFactory()
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    @pytest.fixture
    def anonymous_client(self):
        """Create an anonymous API client."""
        return APIClient()

    def test_unauthenticated_access_returns_401(self, anonymous_client):
        """
        Test that unauthenticated requests are rejected.
        """
        url = reverse("analytics:dashboard-metrics")
        response = anonymous_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_access_returns_200(self, authenticated_client):
        """
        Test that authenticated users can access the endpoint.
        """
        url = reverse("analytics:dashboard-metrics")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_response_has_correct_structure(self, authenticated_client):
        """
        Test that response contains all required fields.
        """
        url = reverse("analytics:dashboard-metrics")
        response = authenticated_client.get(url)

        data = response.json()

        assert "period_start" in data
        assert "period_end" in data
        assert "metrics_history" in data
        assert "status_distribution" in data
        assert "top_products" in data

    def test_default_days_parameter(self, authenticated_client):
        """
        Test that default days parameter is 7.
        """
        url = reverse("analytics:dashboard-metrics")
        response = authenticated_client.get(url)

        data = response.json()
        assert len(data["metrics_history"]) == 7

    def test_custom_days_parameter(self, authenticated_client):
        """
        Test that custom days parameter works correctly.
        """
        url = reverse("analytics:dashboard-metrics")
        response = authenticated_client.get(url, {"days": 30})

        data = response.json()
        assert len(data["metrics_history"]) == 30

    def test_days_parameter_validation_negative(self, authenticated_client):
        """
        Test that negative days parameter is rejected.
        """
        url = reverse("analytics:dashboard-metrics")
        response = authenticated_client.get(url, {"days": -5})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.json()

    def test_days_parameter_validation_zero(self, authenticated_client):
        """
        Test that zero days parameter is rejected.
        """
        url = reverse("analytics:dashboard-metrics")
        response = authenticated_client.get(url, {"days": 0})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_days_parameter_validation_exceeds_maximum(self, authenticated_client):
        """
        Test that days parameter exceeding 90 is rejected.
        """
        url = reverse("analytics:dashboard-metrics")
        response = authenticated_client.get(url, {"days": 100})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_days_parameter_validation_non_integer(self, authenticated_client):
        """
        Test that non-integer days parameter is rejected.
        """
        url = reverse("analytics:dashboard-metrics")
        response = authenticated_client.get(url, {"days": "invalid"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_response_with_actual_data(self, authenticated_client):
        """
        Test endpoint returns actual data when sales exist.
        """
        from datetime import datetime

        today = timezone.now().date()
        test_time = timezone.make_aware(
            datetime.combine(today, datetime.min.time().replace(hour=12))
        )

        customer = CustomerFactory()
        lot = ProductLotFactory(quantity=100)
        sale = SaleFactory(
            customer=customer, created_at=test_time, total_value=Decimal("100.00")
        )
        SaleItemFactory(sale=sale, lot=lot, quantity=1, unit_price=Decimal("100.00"))

        url = reverse("analytics:dashboard-metrics")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        data = response.json()

        assert len(data["metrics_history"]) == 7
        assert any(day["total_revenue"] > 0 for day in data["metrics_history"])
