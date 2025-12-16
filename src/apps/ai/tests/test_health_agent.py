"""Tests for AI Health Agent."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from src.apps.ai.agents.health_agent import (
    HealthAssistantService,
    HealthInsightRequest,
)
from src.apps.health.factories import HealthRecordFactory
from src.apps.pets.factories import BreedFactory, PetFactory


@pytest.mark.django_db
class TestHealthAssistantService:
    """Test HealthAssistantService."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        with patch("src.apps.ai.agents.health_agent.ChatGoogleGenerativeAI"):
            return HealthAssistantService()

    @pytest.fixture
    def pet_with_records(self):
        """Create pet with health records."""
        breed = BreedFactory(name="Labrador", species="dog")
        pet = PetFactory(
            breed=breed, birth_date=timezone.now().date() - timedelta(days=365 * 3)
        )

        # Create various health records
        HealthRecordFactory(
            pet=pet,
            record_type="vaccine",
            description="Vacina antirrábica",
            record_date=timezone.now().date() - timedelta(days=30),
        )
        HealthRecordFactory(
            pet=pet,
            record_type="consultation",
            description="Check-up geral",
            record_date=timezone.now().date() - timedelta(days=60),
        )
        HealthRecordFactory(
            pet=pet,
            record_type="surgery",
            description="Castração",
            record_date=timezone.now().date() - timedelta(days=365),
        )

        return pet

    def test_analyze_pet_health_success(self, service, pet_with_records):
        """Should analyze pet health and return insights."""
        request = HealthInsightRequest(
            pet_id=pet_with_records.id, analysis_period_days=180
        )

        # Mock pattern detection
        service._detect_health_patterns = MagicMock(
            return_value=[
                {
                    "pattern_type": "regular_checkups",
                    "description": "Pet mantém rotina de consultas regulares",
                    "confidence_score": 0.9,
                    "recommendations": ["Continue com check-ups semestrais"],
                }
            ]
        )

        # Mock alerts
        service._generate_health_alerts = MagicMock(return_value=[])

        # Mock save
        service._save_health_insights = MagicMock()

        # Execute
        response = service.analyze_pet_health(request)

        # Assertions
        assert len(response.patterns) == 1
        assert len(response.alerts) == 0
        assert len(response.recommendations) > 0
        assert 0 <= response.health_score <= 100

    def test_analyze_pet_health_pet_not_found(self, service):
        """Should raise error when pet doesn't exist."""
        from src.apps.pets.models import Pet

        request = HealthInsightRequest(pet_id=99999)

        with pytest.raises(Pet.DoesNotExist):
            service.analyze_pet_health(request)

    def test_detect_health_patterns_no_records(self, service):
        """Should return empty patterns when no records."""
        pet = PetFactory()

        patterns = service._detect_health_patterns(pet, pet.health_records.all())

        assert patterns == []

    def test_detect_health_patterns_with_records(self, service, pet_with_records):
        """Should detect patterns from health records."""
        with patch("requests.post") as mock_post:
            # Mock API response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"pattern_type": "vaccination_schedule", "description": "Vacinação em dia", "confidence_score": 0.85, "recommendations": ["Manter calendário"]}'
                                }
                            ]
                        },
                        "groundingMetadata": {"searchQueries": ["pet vaccination"]},
                    }
                ]
            }

            patterns = service._detect_health_patterns(
                pet_with_records, pet_with_records.health_records.all()
            )

            assert len(patterns) > 0
            assert patterns[0]["pattern_type"] == "vaccination_schedule"
            assert patterns[0]["confidence_score"] == 0.85

    def test_detect_health_patterns_api_error(self, service, pet_with_records):
        """Should handle API errors gracefully."""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = Exception("API Error")

            patterns = service._detect_health_patterns(
                pet_with_records, pet_with_records.health_records.all()
            )

            assert patterns == []

    def test_generate_health_alerts_vaccine_overdue(self, service):
        """Should generate alert for overdue vaccine."""
        pet = PetFactory()
        HealthRecordFactory(
            pet=pet,
            record_type="vaccine",
            record_date=timezone.now().date() - timedelta(days=400),
        )

        alerts = service._generate_health_alerts(pet)

        assert len(alerts) > 0
        assert any(a["type"] == "vaccine_overdue" for a in alerts)
        assert any(a["severity"] == "high" for a in alerts)

    def test_generate_health_alerts_vaccine_due_soon(self, service):
        """Should generate alert when vaccine is due soon."""
        pet = PetFactory()
        HealthRecordFactory(
            pet=pet,
            record_type="vaccine",
            record_date=timezone.now().date() - timedelta(days=340),
        )

        alerts = service._generate_health_alerts(pet)

        assert len(alerts) > 0
        assert any(a["type"] == "vaccine_due_soon" for a in alerts)
        assert any(a["severity"] == "medium" for a in alerts)

    def test_generate_health_alerts_checkup_recommended(self, service):
        """Should recommend checkup if none in 6 months."""
        pet = PetFactory()
        HealthRecordFactory(
            pet=pet,
            record_type="consultation",
            record_date=timezone.now().date() - timedelta(days=200),
        )

        alerts = service._generate_health_alerts(pet)

        assert any(a["type"] == "checkup_recommended" for a in alerts)

    def test_generate_health_alerts_no_records(self, service):
        """Should recommend checkup when no records exist."""
        pet = PetFactory()

        alerts = service._generate_health_alerts(pet)

        assert any(a["type"] == "checkup_recommended" for a in alerts)

    def test_generate_recommendations_from_patterns(self, service):
        """Should extract recommendations from patterns."""
        pet = PetFactory()
        patterns = [
            {"recommendations": ["Recomendação 1", "Recomendação 2"]},
            {"recommendations": ["Recomendação 3"]},
        ]
        alerts = []

        recommendations = service._generate_recommendations(pet, patterns, alerts)

        assert len(recommendations) >= 3

    def test_generate_recommendations_from_alerts(self, service):
        """Should generate recommendations from alerts."""
        pet = PetFactory()
        patterns = []
        alerts = [
            {"type": "vaccine_overdue"},
            {"type": "checkup_recommended"},
        ]

        recommendations = service._generate_recommendations(pet, patterns, alerts)

        assert "Agende vacinação o mais rápido possível" in recommendations
        assert "Agende check-up veterinário preventivo" in recommendations

    def test_generate_recommendations_senior_pet(self, service):
        """Should add senior pet recommendations."""
        pet = PetFactory(birth_date=timezone.now().date() - timedelta(days=365 * 8))
        patterns = []
        alerts = []

        recommendations = service._generate_recommendations(pet, patterns, alerts)

        assert any("sênior" in r.lower() for r in recommendations)

    def test_generate_recommendations_deduplication(self, service):
        """Should remove duplicate recommendations."""
        pet = PetFactory()
        patterns = [
            {"recommendations": ["Recomendação 1", "Recomendação 1"]},
        ]
        alerts = []

        recommendations = service._generate_recommendations(pet, patterns, alerts)

        assert recommendations.count("Recomendação 1") == 1

    def test_calculate_health_score_perfect(self, service):
        """Should calculate 100 score for perfect health."""
        pet = PetFactory()

        # Recent checkup
        HealthRecordFactory(
            pet=pet,
            record_type="consultation",
            record_date=timezone.now().date() - timedelta(days=30),
        )

        # Recent vaccine
        HealthRecordFactory(
            pet=pet,
            record_type="vaccine",
            record_date=timezone.now().date() - timedelta(days=60),
        )

        # Multiple records in last year
        for i in range(3):
            HealthRecordFactory(
                pet=pet,
                record_type="consultation",
                record_date=timezone.now().date() - timedelta(days=90 * i),
            )

        health_records = pet.health_records.all()
        alerts = []

        score = service._calculate_health_score(pet, health_records, alerts)

        assert score == 100.0

    def test_calculate_health_score_with_alerts(self, service):
        """Should reduce score with high-severity alerts."""
        pet = PetFactory()
        health_records = pet.health_records.all()
        alerts = [{"severity": "high"}]

        score = service._calculate_health_score(pet, health_records, alerts)

        assert score < 100

    def test_calculate_health_score_no_vaccine(self, service):
        """Should reduce score without recent vaccine."""
        pet = PetFactory()
        HealthRecordFactory(
            pet=pet,
            record_type="vaccine",
            record_date=timezone.now().date() - timedelta(days=400),
        )

        health_records = pet.health_records.all()
        alerts = []

        score = service._calculate_health_score(pet, health_records, alerts)

        assert score <= 70  # Missing vaccine points

    def test_calculate_health_score_partial_monitoring(self, service):
        """Should give partial points for some monitoring."""
        pet = PetFactory()
        HealthRecordFactory(
            pet=pet,
            record_type="consultation",
            record_date=timezone.now().date() - timedelta(days=100),
        )

        health_records = pet.health_records.all()
        alerts = []

        score = service._calculate_health_score(pet, health_records, alerts)

        assert 0 < score < 100

    def test_save_health_insights(self, service):
        """Should save insights to database."""
        from src.apps.ai.models import AIGeneratedContent

        pet = PetFactory()
        patterns = [{"pattern_type": "test", "confidence_score": 0.8}]
        recommendations = ["Recomendação 1"]

        service._save_health_insights(pet, patterns, recommendations, user=None)

        content = AIGeneratedContent.objects.filter(pet=pet).last()
        assert content is not None
        assert content.content_type == "health_insight"
        assert content.confidence_score == 0.8

    def test_generate_health_report_success(self, service, pet_with_records):
        """Should generate comprehensive health report."""
        from langchain_core.messages import AIMessage

        mock_response = AIMessage(
            content="Relatório completo de saúde do pet mostrando bom estado geral."
        )
        service.llm.invoke = MagicMock(return_value=mock_response)

        report = service.generate_health_report(pet_with_records.id, period_days=365)

        assert report != ""
        assert "bom estado geral" in report.lower()

    def test_generate_health_report_pet_not_found(self, service):
        """Should raise error for non-existent pet."""
        from src.apps.pets.models import Pet

        with pytest.raises(Pet.DoesNotExist):
            service.generate_health_report(99999)

    def test_generate_health_report_llm_error(self, service, pet_with_records):
        """Should raise error when LLM fails."""
        service.llm.invoke = MagicMock(side_effect=Exception("LLM Error"))

        with pytest.raises(Exception, match="LLM Error"):
            service.generate_health_report(pet_with_records.id)
