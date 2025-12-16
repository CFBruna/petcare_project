"""Tests for Pets Admin."""

from unittest.mock import MagicMock, patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from src.apps.ai.agents.health_agent import HealthInsightResponse
from src.apps.pets.admin import PetAdmin
from src.apps.pets.factories import PetFactory
from src.apps.pets.models import Pet

User = get_user_model()


@pytest.mark.django_db
class TestPetAdmin:
    """Test PetAdmin."""

    @pytest.fixture
    def admin_site(self):
        """Create admin site."""
        return AdminSite()

    @pytest.fixture
    def pet_admin(self, admin_site):
        """Create PetAdmin instance."""
        return PetAdmin(Pet, admin_site)

    @pytest.fixture
    def staff_user(self):
        """Create staff user."""
        return User.objects.create_user(
            username="admin", password="pass", is_staff=True, is_superuser=True
        )

    @pytest.fixture
    def factory(self):
        """Create request factory."""
        return RequestFactory()

    def test_analyze_health_patterns_success(self, pet_admin, factory, staff_user):
        """Should analyze health patterns for selected pets."""
        pet1 = PetFactory(name="Rex")
        pet2 = PetFactory(name="Max")
        queryset = Pet.objects.filter(id__in=[pet1.id, pet2.id])

        request = factory.post("/admin/pets/pet/")
        request.user = staff_user
        request._messages = MagicMock()

        # Patch where it's imported (inside the function)
        with patch(
            "src.apps.ai.agents.health_agent.HealthAssistantService"
        ) as MockService:
            mock_service = MagicMock()
            MockService.return_value = mock_service

            mock_service.analyze_pet_health.return_value = HealthInsightResponse(
                patterns=[{"type": "test"}],
                alerts=[{" type": "vaccine"}],
                recommendations=["Test recommendation"],
                health_score=85.0,
            )

            pet_admin.analyze_health_patterns(request, queryset)

            # Should call service for each pet
            assert mock_service.analyze_pet_health.call_count == 2

    def test_analyze_health_patterns_with_error(self, pet_admin, factory, staff_user):
        """Should handle errors gracefully."""
        pet = PetFactory(name="Rex")
        queryset = Pet.objects.filter(id=pet.id)

        request = factory.post("/admin/pets/pet/")
        request.user = staff_user
        request._messages = MagicMock()

        with patch(
            "src.apps.ai.agents.health_agent.HealthAssistantService"
        ) as MockService:
            mock_service = MagicMock()
            MockService.return_value = mock_service
            mock_service.analyze_pet_health.side_effect = Exception("Analysis failed")

            pet_admin.analyze_health_patterns(request, queryset)

            # Should handle error without crashing
            assert mock_service.analyze_pet_health.call_count == 1

    def test_analyze_health_patterns_mixed_results(
        self, pet_admin, factory, staff_user
    ):
        """Should handle mixed success and errors."""
        pet1 = PetFactory(name="Rex")
        pet2 = PetFactory(name="Max")
        queryset = Pet.objects.filter(id__in=[pet1.id, pet2.id])

        request = factory.post("/admin/pets/pet/")
        request.user = staff_user
        request._messages = MagicMock()

        with patch(
            "src.apps.ai.agents.health_agent.HealthAssistantService"
        ) as MockService:
            mock_service = MagicMock()
            MockService.return_value = mock_service

            # First call succeeds, second fails
            mock_service.analyze_pet_health.side_effect = [
                HealthInsightResponse(
                    patterns=[],
                    alerts=[],
                    recommendations=[],
                    health_score=90.0,
                ),
                Exception("Error"),
            ]

            pet_admin.analyze_health_patterns(request, queryset)

            # Should call service for both pets
            assert mock_service.analyze_pet_health.call_count == 2
