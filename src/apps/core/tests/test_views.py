from unittest.mock import mock_open, patch

import pytest
from django.db import models
from django.test import RequestFactory

from src.apps.core.views import AutoSchemaModelNameMixin, DashboardView


class DummyModel(models.Model):
    objects = models.Manager()

    class Meta:
        app_label = "core"
        verbose_name = "Dummy"
        verbose_name_plural = "Dummies"


class DummyViewSet(AutoSchemaModelNameMixin):
    queryset = DummyModel.objects.all()  # type: ignore[misc]


@pytest.mark.django_db
class TestAutoSchemaModelNameMixin:
    def test_get_model_name_singular(self):
        mixin = DummyViewSet()
        assert mixin._get_model_name() == "Dummy"

    def test_get_model_name_plural(self):
        mixin = DummyViewSet()
        assert mixin._get_model_name(plural=True) == "Dummies"

    def test_get_model_name_no_queryset_returns_empty(self):
        class NoQuerySetViewSet(AutoSchemaModelNameMixin):
            queryset = None

        mixin = NoQuerySetViewSet()
        assert mixin._get_model_name() == ""


@pytest.mark.django_db
class TestDashboardView:
    """Test DashboardView."""

    @pytest.fixture
    def factory(self):
        """Create request factory."""
        return RequestFactory()

    def test_dashboard_serves_file(self, factory):
        """Should serve dashboard HTML file."""
        request = factory.get("/dashboard/")
        view = DashboardView()

        mock_html = "<html><body>Dashboard</body></html>"

        with patch("builtins.open", mock_open(read_data=mock_html)):
            response = view.get(request)

            assert response.status_code == 200
            assert response.content.decode() == mock_html
            assert response["Content-Type"] == "text/html"

    def test_dashboard_file_not_found(self, factory):
        """Should return 404 when dashboard not built."""
        request = factory.get("/dashboard/")
        view = DashboardView()

        with patch("builtins.open", side_effect=FileNotFoundError()):
            response = view.get(request)

            assert response.status_code == 404
            assert "not built" in response.content.decode()


@pytest.mark.django_db
class TestHealthCheckView:
    """Test HealthCheckView."""

    def test_health_check_returns_ok(self, client):
        """Should return OK status."""
        response = client.get("/api/v1/status/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "petcare"
