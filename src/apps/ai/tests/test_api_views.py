"""Tests for AI API AJAX views."""

import json
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model

from src.apps.ai.agents.health_agent import HealthInsightResponse
from src.apps.ai.services import ProductDescriptionResponse
from src.apps.pets.factories import PetFactory

User = get_user_model()


@pytest.mark.django_db
class TestProductDescriptionAjaxView:
    """Test generate_product_description_ajax view."""

    @pytest.fixture
    def staff_user(self):
        """Create staff user."""
        return User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )

    @pytest.fixture
    def client_logged_in(self, client, staff_user):
        """Create logged in client."""
        client.force_login(staff_user)
        return client

    def test_generate_description_success(self, client_logged_in):
        """Should generate product description successfully."""
        with patch("src.apps.ai.api.views.ProductIntelligenceService") as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance

            mock_service_instance.generate_description.return_value = (
                ProductDescriptionResponse(
                    description="Test description",
                    confidence_score=0.9,
                    is_known_product=True,
                    similar_products=["Product 1"],
                    suggestions={"seo_title": "Test"},
                )
            )

            response = client_logged_in.post(
                "/admin/ai/generate-product-description/",
                data=json.dumps(
                    {
                        "product_name": "Test Product",
                        "category": "Test Category",
                        "brand": "Test Brand",
                        "price": 100.0,
                        "mode": "technical",
                    }
                ),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["description"] == "Test description"
            assert data["confidence_score"] == 0.9

    def test_generate_description_missing_product_name(self, client_logged_in):
        """Should return error when product name is missing."""
        response = client_logged_in.post(
            "/admin/ai/generate-product-description/",
            data=json.dumps({"category": "Test"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "required" in data["error"].lower()

    def test_generate_description_service_error(self, client_logged_in):
        """Should handle service errors gracefully."""
        with patch("src.apps.ai.api.views.ProductIntelligenceService") as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.generate_description.side_effect = Exception(
                "Service error"
            )

            response = client_logged_in.post(
                "/admin/ai/generate-product-description/",
                data=json.dumps({"product_name": "Test Product"}),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "error" in data

    def test_generate_description_requires_staff(self, client):
        """Should require staff permissions."""
        # Create non-staff user
        user = User.objects.create_user(username="user", password="pass")
        client.force_login(user)

        response = client.post(
            "/admin/ai/generate-product-description/",
            data=json.dumps({"product_name": "Test"}),
            content_type="application/json",
        )

        # Should redirect to login or return forbidden
        assert response.status_code in [302, 403]

    def test_generate_description_requires_post(self, client_logged_in):
        """Should require POST method."""
        response = client_logged_in.get("/admin/ai/generate-product-description/")

        assert response.status_code == 405


@pytest.mark.django_db
class TestPetHealthAjaxView:
    """Test analyze_pet_health_ajax view."""

    @pytest.fixture
    def staff_user(self):
        """Create staff user."""
        return User.objects.create_user(
            username="staff", password="pass", is_staff=True
        )

    @pytest.fixture
    def client_logged_in(self, client, staff_user):
        """Create logged in client."""
        client.force_login(staff_user)
        return client

    @pytest.fixture
    def pet(self):
        """Create pet."""
        return PetFactory()

    def test_analyze_health_success(self, client_logged_in, pet):
        """Should analyze pet health successfully."""
        with patch("src.apps.ai.api.views.HealthAssistantService") as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance

            mock_service_instance.analyze_pet_health.return_value = (
                HealthInsightResponse(
                    patterns=[
                        {
                            "pattern_type": "regular_checkups",
                            "description": "Good health pattern",
                            "confidence_score": 0.9,
                        }
                    ],
                    alerts=[{"type": "vaccine_due", "severity": "low"}],
                    recommendations=["Continue regular checkups"],
                    health_score=85.0,
                )
            )

            response = client_logged_in.post(
                "/admin/ai/analyze-pet-health/",
                data=json.dumps({"pet_id": pet.id}),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["health_score"] == 85.0
            assert len(data["patterns"]) == 1
            assert len(data["alerts"]) == 1
            assert len(data["recommendations"]) == 1

    def test_analyze_health_missing_pet_id(self, client_logged_in):
        """Should return error when pet_id is missing."""
        response = client_logged_in.post(
            "/admin/ai/analyze-pet-health/",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "required" in data["error"].lower()

    def test_analyze_health_service_error(self, client_logged_in, pet):
        """Should handle service errors gracefully."""
        with patch("src.apps.ai.api.views.HealthAssistantService") as MockService:
            mock_service_instance = MagicMock()
            MockService.return_value = mock_service_instance
            mock_service_instance.analyze_pet_health.side_effect = Exception(
                "Analysis error"
            )

            response = client_logged_in.post(
                "/admin/ai/analyze-pet-health/",
                data=json.dumps({"pet_id": pet.id}),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "error" in data

    def test_analyze_health_requires_staff(self, client, pet):
        """Should require staff permissions."""
        user = User.objects.create_user(username="user", password="pass")
        client.force_login(user)

        response = client.post(
            "/admin/ai/analyze-pet-health/",
            data=json.dumps({"pet_id": pet.id}),
            content_type="application/json",
        )

        assert response.status_code in [302, 403]

    def test_analyze_health_requires_post(self, client_logged_in):
        """Should require POST method."""
        response = client_logged_in.get("/admin/ai/analyze-pet-health/")

        assert response.status_code == 405
