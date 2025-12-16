"""Health Assistant Agent - Service Layer."""

import json
from dataclasses import dataclass
from datetime import timedelta

import structlog
from django.conf import settings
from django.utils import timezone
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src.apps.ai.models import AIGeneratedContent, HealthPattern
from src.apps.ai.prompts import health_prompts

logger = structlog.get_logger(__name__)


@dataclass
class HealthInsightRequest:
    """DTO for health insight generation request."""

    pet_id: int
    analysis_period_days: int = 180  # Last 6 months by default


@dataclass
class HealthInsightResponse:
    """DTO for health insight generation response."""

    patterns: list[dict]
    alerts: list[dict]
    recommendations: list[str]
    health_score: float


class HealthAssistantService:
    """
    Service Layer for Health Assistant Agent.

    Responsibilities:
    - Analyze health patterns from pet records
    - Generate health insights and alerts
    - Detect seasonal/recurring conditions
    - Suggest preventive actions
    """

    def __init__(self):
        """Initialize LLM."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL_NAME,
            temperature=0.5,  # Lower temperature for health analysis
            google_api_key=settings.GOOGLE_API_KEY,
        )

    def analyze_pet_health(
        self, request: HealthInsightRequest, user=None
    ) -> HealthInsightResponse:
        """
        Analyze pet health and generate insights.

        Flow:
        1. Fetch health records
        2. Detect patterns
        3. Generate alerts
        4. Create recommendations
        5. Calculate health score
        """
        from src.apps.pets.models import Pet

        logger.info("analyze_pet_health_started", pet_id=request.pet_id)

        try:
            pet = Pet.objects.get(id=request.pet_id)
        except Pet.DoesNotExist:
            logger.error("pet_not_found", pet_id=request.pet_id)
            raise

        # 1. Fetch health records
        cutoff_date = timezone.now() - timedelta(days=request.analysis_period_days)
        health_records = pet.health_records.filter(
            record_date__gte=cutoff_date
        ).order_by("-record_date")

        # 2. Detect patterns
        patterns = self._detect_health_patterns(pet, health_records)

        # 3. Generate alerts
        alerts = self._generate_health_alerts(pet)

        # 4. Create recommendations
        recommendations = self._generate_recommendations(pet, patterns, alerts)

        # 5. Calculate health score
        health_score = self._calculate_health_score(pet, health_records, alerts)

        # Save insights
        self._save_health_insights(pet, patterns, recommendations, user)

        logger.info(
            "analyze_pet_health_completed",
            pet_id=request.pet_id,
            patterns_count=len(patterns),
            alerts_count=len(alerts),
        )

        return HealthInsightResponse(
            patterns=patterns,
            alerts=alerts,
            recommendations=recommendations,
            health_score=health_score,
        )

    def _detect_health_patterns(self, pet, health_records) -> list[dict]:
        """Detect patterns in health records using LLM."""
        if not health_records.exists():
            return []

        # Group records by type
        record_summary = []
        for record in health_records[:10]:  # Last 10 records
            record_summary.append(
                f"- {record.record_date.strftime('%d/%m/%Y')}: "
                f"{record.get_record_type_display()} - {record.description}"
            )

        records_text = "\n".join(record_summary)

        # Calculate age
        age = (
            (timezone.now().date() - pet.birth_date).days // 365
            if pet.birth_date
            else 0
        )

        try:
            # Use REST API directly for Google Search Grounding
            # The SDK version we have (google-generativeai 0.8.5) doesn't support the new google_search syntax
            import requests

            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL_NAME}:generateContent"

            prompt_text = (
                f"{health_prompts.HEALTH_PATTERN_ANALYSIS_SYSTEM}\n\n"
                f"{health_prompts.HEALTH_PATTERN_ANALYSIS_USER.format(pet_name=pet.name, species=pet.breed.get_species_display() if pet.breed else 'Não especificada', breed=pet.breed.name if pet.breed else 'Não especificada', age=age, health_records=records_text)}"
            )

            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "tools": [{"google_search": {}}],
            }

            headers = {
                "x-goog-api-key": settings.GOOGLE_API_KEY,
                "Content-Type": "application/json",
            }

            logger.info("llm_grounding_search_started", pet_id=pet.id)

            response = requests.post(api_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()

            result = response.json()

            # Check if grounding was used
            grounding_metadata = result.get("candidates", [{}])[0].get(
                "groundingMetadata"
            )
            logger.info(
                "llm_response_received",
                pet_id=pet.id,
                grounding_used=bool(grounding_metadata),
                grounding_metadata=str(grounding_metadata)
                if grounding_metadata
                else "None",
            )

            # Extract text from response
            content_text = (
                result.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            # Parse JSON from response
            try:
                start_idx = content_text.find("{")
                end_idx = content_text.rfind("}") + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = content_text[start_idx:end_idx]
                    pattern_data = json.loads(json_str)
                else:
                    logger.warning("grounding_response_no_json", content=content_text)
                    pattern_data = {
                        "pattern_type": "consultation_required",
                        "description": content_text[:500],
                        "confidence_score": 0.8,
                        "recommendations": ["Verificar relatório detalhado"],
                    }
            except Exception as e:
                logger.error("json_parse_error", error=str(e))
                pattern_data = {
                    "pattern_type": "error",
                    "description": "Erro ao processar dados da IA.",
                    "confidence_score": 0,
                }

            # Save pattern to database
            if pattern_data.get("confidence_score", 0) > 0.6:
                HealthPattern.objects.update_or_create(
                    pet=pet,
                    pattern_type=pattern_data.get("pattern_type", "observation"),
                    defaults={
                        "description": pattern_data.get("description", "Sem descrição"),
                        "confidence_score": pattern_data.get("confidence_score", 0.0),
                        "recommendations": pattern_data.get("recommendations", []),
                        "is_active": True,
                    },
                )

            return [pattern_data]

        except Exception as e:
            logger.error("detect_health_patterns_failed", pet_id=pet.id, error=str(e))
            return []

    def _generate_health_alerts(self, pet) -> list[dict]:
        """Generate health alerts (vaccines, checkups, etc)."""
        alerts = []

        # Check vaccine status

        last_vaccine = (
            pet.health_records.filter(record_type="vaccine")
            .order_by("-record_date")
            .first()
        )

        if last_vaccine:
            days_since_vaccine = (timezone.now().date() - last_vaccine.record_date).days

            if days_since_vaccine > 365:
                alerts.append(
                    {
                        "type": "vaccine_overdue",
                        "severity": "high",
                        "title": "Vacina Atrasada",
                        "message": f"Última vacina foi há {days_since_vaccine} dias. Agende uma consulta veterinária.",
                        "days_overdue": days_since_vaccine - 365,
                    }
                )
            elif days_since_vaccine > 330:
                alerts.append(
                    {
                        "type": "vaccine_due_soon",
                        "severity": "medium",
                        "title": "Vacina Próxima do Vencimento",
                        "message": f"Próxima vacina deve ser aplicada em breve (última há {days_since_vaccine} dias).",
                        "days_until_due": 365 - days_since_vaccine,
                    }
                )

        # Check if pet has recent checkup
        last_checkup = (
            pet.health_records.filter(record_type="consultation")
            .order_by("-record_date")
            .first()
        )

        if (
            not last_checkup
            or (timezone.now().date() - last_checkup.record_date).days > 180
        ):
            alerts.append(
                {
                    "type": "checkup_recommended",
                    "severity": "low",
                    "title": "Check-up Recomendado",
                    "message": "Recomendamos um check-up veterinário semestral para manter a saúde do seu pet.",
                }
            )

        return alerts

    def _generate_recommendations(
        self, pet, patterns: list[dict], alerts: list[dict]
    ) -> list[str]:
        """Generate actionable recommendations based on patterns and alerts."""
        recommendations = []

        # From patterns
        for pattern in patterns:
            if "recommendations" in pattern:
                recommendations.extend(pattern["recommendations"])

        # From alerts
        for alert in alerts:
            if alert["type"] == "vaccine_overdue":
                recommendations.append("Agende vacinação o mais rápido possível")
            elif alert["type"] == "checkup_recommended":
                recommendations.append("Agende check-up veterinário preventivo")

        # General recommendations based on age
        age = (
            (timezone.now().date() - pet.birth_date).days // 365
            if pet.birth_date
            else 0
        )

        if age > 7:
            recommendations.append(
                "Pet sênior: considere exames de sangue anuais para detecção precoce de problemas"
            )

        return list(set(recommendations))  # Remove duplicates

    def _calculate_health_score(self, pet, health_records, alerts: list[dict]) -> float:
        """
        Calculate health score (0-100).

        Factors:
        - Recent checkups: +20
        - Vaccines up to date: +30
        - No high-severity alerts: +30
        - Regular health monitoring: +20
        """
        score = 0.0

        # Recent checkup
        last_checkup = (
            health_records.filter(record_type="consultation")
            .order_by("-record_date")
            .first()
        )
        if (
            last_checkup
            and (timezone.now().date() - last_checkup.record_date).days < 180
        ):
            score += 20

        # Vaccines
        last_vaccine = (
            health_records.filter(record_type="vaccine")
            .order_by("-record_date")
            .first()
        )
        if (
            last_vaccine
            and (timezone.now().date() - last_vaccine.record_date).days < 365
        ):
            score += 30

        # Alerts
        high_severity_alerts = [a for a in alerts if a.get("severity") == "high"]
        if not high_severity_alerts:
            score += 30
        elif len(high_severity_alerts) == 1:
            score += 15

        # Regular monitoring
        records_last_year = health_records.filter(
            record_date__gte=timezone.now() - timedelta(days=365)
        ).count()
        if records_last_year >= 3:
            score += 20
        elif records_last_year >= 1:
            score += 10

        return min(score, 100.0)

    def _save_health_insights(
        self, pet, patterns: list[dict], recommendations: list[str], user=None
    ) -> None:
        """Save health insights for audit."""
        insight_text = f"Padrões detectados: {len(patterns)}\n"
        insight_text += f"Recomendações: {', '.join(recommendations)}"

        AIGeneratedContent.objects.create(
            content_type="health_insight",
            input_data={"pet_id": pet.id, "pet_name": pet.name},
            generated_content=insight_text,
            model_used=settings.GEMINI_MODEL_NAME,
            confidence_score=patterns[0].get("confidence_score", 0.5)
            if patterns
            else 0.5,
            pet=pet,
            created_by=user,
        )

    def generate_health_report(self, pet_id: int, period_days: int = 365) -> str:
        """Generate comprehensive health report for a pet."""
        from src.apps.pets.models import Pet

        logger.info("generate_health_report_started", pet_id=pet_id)

        try:
            pet = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist:
            logger.error("pet_not_found", pet_id=pet_id)
            raise

        cutoff_date = timezone.now() - timedelta(days=period_days)
        health_records = pet.health_records.filter(record_date__gte=cutoff_date)

        # Count by type
        consultations = health_records.filter(record_type="consultation").count()
        vaccines = health_records.filter(record_type="vaccine").count()
        surgeries = health_records.filter(record_type="surgery").count()

        # Build detailed records
        detailed_records = []
        for record in health_records.order_by("-record_date")[:20]:
            detailed_records.append(
                f"- {record.record_date.strftime('%d/%m/%Y')}: "
                f"{record.get_record_type_display()} - {record.description}"
            )

        records_text = "\n".join(detailed_records)

        try:
            messages = [
                SystemMessage(content=health_prompts.HEALTH_REPORT_SYSTEM),
                HumanMessage(
                    content=health_prompts.HEALTH_REPORT_USER.format(
                        pet_name=pet.name,
                        period=f"Últimos {period_days} dias",
                        consultations_count=consultations,
                        vaccines_count=vaccines,
                        surgeries_count=surgeries,
                        detailed_records=records_text,
                    )
                ),
            ]

            response = self.llm.invoke(messages)
            report = response.content.strip()

            logger.info("generate_health_report_completed", pet_id=pet_id)
            return report

        except Exception as e:
            logger.error("generate_health_report_failed", pet_id=pet_id, error=str(e))
            raise
