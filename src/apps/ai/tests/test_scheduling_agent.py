from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone
from langchain_core.messages import AIMessage

from src.apps.accounts.factories import CustomerFactory
from src.apps.ai.agents.scheduling_agent import (
    SchedulingAgentService,
    SchedulingIntentRequest,
)
from src.apps.ai.agents.tools import (
    calculate_price,
    check_availability,
    search_customer_pets,
)
from src.apps.pets.factories import BreedFactory, PetFactory
from src.apps.schedule.factories import ServiceFactory, TimeSlotFactory


@pytest.mark.django_db
class TestSchedulingAgentTools:
    """Test individual tools used by the scheduling agent."""

    def test_search_customer_pets_by_breed(self):
        """Should find pets by breed."""
        breed = BreedFactory(name="Golden Retriever", species="DOG")
        customer = CustomerFactory()
        pet = PetFactory(
            name="Thor",
            breed=breed,
            owner=customer,
            birth_date=date(2019, 1, 1),
        )

        results = search_customer_pets(breed="golden")

        assert len(results) == 1
        assert results[0]["id"] == pet.id
        assert results[0]["name"] == "Thor"
        assert results[0]["breed"] == "Golden Retriever"
        assert results[0]["species"] == "Cachorro"

    def test_search_customer_pets_by_species_portuguese(self):
        """Should find pets by species in Portuguese."""
        breed = BreedFactory(name="Siamês", species="CAT")
        customer = CustomerFactory()
        PetFactory(name="Mia", breed=breed, owner=customer)

        results = search_customer_pets(species="gato")

        assert len(results) == 1
        assert results[0]["species"] == "Gato"

    def test_search_customer_pets_by_age(self):
        """Should filter pets by age range."""
        breed = BreedFactory(name="Labrador", species="DOG")
        customer = CustomerFactory()

        PetFactory(
            name="Max",
            breed=breed,
            owner=customer,
            birth_date=date.today() - timedelta(days=5 * 365),
        )

        PetFactory(
            name="Buddy",
            breed=breed,
            owner=customer,
            birth_date=date.today() - timedelta(days=10 * 365),
        )

        results = search_customer_pets(breed="labrador", age_min=4, age_max=6)

        assert len(results) == 1
        assert results[0]["name"] == "Max"

    def test_search_customer_pets_by_customer_id(self):
        """Should filter pets by customer ID."""
        breed = BreedFactory(name="Poodle", species="DOG")
        customer1 = CustomerFactory()
        customer2 = CustomerFactory()

        pet1 = PetFactory(name="Rex", breed=breed, owner=customer1)
        PetFactory(name="Luna", breed=breed, owner=customer2)

        results = search_customer_pets(customer_id=customer1.id)

        assert len(results) == 1
        assert results[0]["id"] == pet1.id

    def test_search_customer_pets_no_results(self):
        """Should return empty list when no pets match."""
        results = search_customer_pets(breed="Dinossauro")

        assert results == []

    def test_check_availability_weekday_portuguese(self):
        """Should parse Portuguese weekday names."""
        TimeSlotFactory(day_of_week=5, start_time="08:00", end_time="20:00")
        service = ServiceFactory(duration_minutes=60)

        result = check_availability(day="sábado", service_name=service.name)

        assert result["day_of_week"] == "Sábado"
        assert len(result["available_slots"]) > 0

    def test_check_availability_with_period_filter(self):
        """Should filter slots by time period."""
        TimeSlotFactory(day_of_week=5, start_time="08:00", end_time="20:00")
        service = ServiceFactory(duration_minutes=60)

        result = check_availability(
            day="sábado", period="morning", service_name=service.name
        )

        for slot in result["available_slots"]:
            hour = int(slot["time"].split(":")[0])
            assert hour < 12

    def test_check_availability_iso_date(self):
        """Should parse ISO date format."""
        future_date = (timezone.now() + timedelta(days=7)).date()
        weekday = future_date.weekday()

        TimeSlotFactory(day_of_week=weekday, start_time="08:00", end_time="20:00")
        service = ServiceFactory(duration_minutes=60)

        result = check_availability(
            day=future_date.isoformat(), service_name=service.name
        )

        assert result["date"] == future_date.strftime("%d/%m/%Y")

    def test_check_availability_no_slots(self):
        """Should handle no available slots."""
        ServiceFactory(duration_minutes=60)

        result = check_availability(day="segunda")

        assert "error" in result or result.get("total_slots", 0) == 0

    def test_calculate_price_with_size_multiplier(self):
        """Should apply size multiplier to base price."""
        ServiceFactory(name="Banho e Tosa", price=100.0, duration_minutes=90)

        result = calculate_price(service_name="banho", pet_size="grande")

        assert result["base_price"] == 100.0
        assert result["final_price"] == 130.0
        assert result["formatted_price"] == "R$ 130.00"
        assert result["duration_minutes"] == 90

    def test_calculate_price_small_pet(self):
        """Should apply discount for small pets."""
        ServiceFactory(name="Consulta", price=100.0)

        result = calculate_price(service_name="consulta", pet_size="pequeno")

        assert result["final_price"] == 80.0

    def test_calculate_price_service_not_found(self):
        """Should handle service not found."""
        result = calculate_price(service_name="Serviço Inexistente", pet_size="médio")

        assert "error" in result
        assert result["price"] is None


@pytest.mark.django_db
class TestSchedulingAgentService:
    """Test SchedulingAgentService."""

    @pytest.fixture
    def service(self):
        """Create service instance with mocked LLM."""
        with patch("src.apps.ai.agents.scheduling_agent.ChatGoogleGenerativeAI"):
            return SchedulingAgentService()

    @pytest.fixture
    def setup_data(self):
        """Create test data."""
        breed = BreedFactory(name="Golden Retriever", species="DOG")
        customer = CustomerFactory()
        pet = PetFactory(
            name="Thor",
            breed=breed,
            owner=customer,
            birth_date=date(2019, 1, 1),
        )
        TimeSlotFactory(day_of_week=5, start_time="08:00", end_time="20:00")  # Saturday
        service = ServiceFactory(name="Banho e Tosa", price=120.0, duration_minutes=90)

        return {"pet": pet, "customer": customer, "service": service}

    def test_generate_intent_with_tool_calls(self, service, setup_data):
        """Should execute tools when LLM requests them."""
        mock_tool_call = {
            "name": "search_customer_pets",
            "args": {"species": "dog", "breed": "golden", "age_min": 5, "age_max": 5},
            "id": "call_123",
        }

        first_response = AIMessage(content="", tool_calls=[mock_tool_call])

        final_response = AIMessage(
            content="Encontrei o Thor! Temos horários disponíveis no sábado."
        )

        service.llm_with_tools.invoke = MagicMock(return_value=first_response)
        service.llm.invoke = MagicMock(return_value=final_response)

        # Execute
        request = SchedulingIntentRequest(
            user_input="Preciso banho e tosa para meu Golden de 5 anos",
            customer_id=setup_data["customer"].id,
        )

        response = service.generate_intent(request)

        # Assertions
        assert "Thor" in response.message
        assert len(response.tools_executed) > 0
        assert response.tools_executed[0].tool_name == "search_customer_pets"
        assert response.confidence_score > 0.0

    def test_generate_intent_no_tool_calls(self, service):
        """Should handle requests without tool calls."""
        mock_response = AIMessage(content="Olá! Como posso ajudar?")
        service.llm_with_tools.invoke = MagicMock(return_value=mock_response)

        request = SchedulingIntentRequest(user_input="Olá")
        response = service.generate_intent(request)

        assert response.message == "Olá! Como posso ajudar?"
        assert len(response.tools_executed) == 0
        assert response.confidence_score == 0.5

    def test_detect_intent_book_appointment(self, service):
        """Should detect booking intent."""
        intent = service._detect_intent("Preciso agendar uma consulta", [])

        assert intent == "book_appointment"

    def test_detect_intent_check_availability(self, service):
        """Should detect availability check intent."""
        from src.apps.ai.agents.scheduling_agent import ToolExecution

        tools = [ToolExecution("check_availability", {}, {}, "")]
        intent = service._detect_intent("Quais horários disponíveis?", tools)

        assert intent == "check_availability"

    def test_calculate_confidence_with_successful_tools(self, service):
        """Should calculate high confidence with successful tools."""
        from src.apps.ai.agents.scheduling_agent import ToolExecution

        tools = [
            ToolExecution("search_customer_pets", {}, [{"id": 1, "name": "Thor"}], ""),
            ToolExecution("check_availability", {}, {"slots": ["09:00"]}, ""),
        ]

        confidence = service._calculate_confidence(tools)

        assert confidence >= 0.9

    def test_calculate_confidence_with_errors(self, service):
        """Should calculate low confidence when tools fail."""
        from src.apps.ai.agents.scheduling_agent import ToolExecution

        tools = [
            ToolExecution("search_customer_pets", {}, {"error": "Pet not found"}, ""),
        ]

        confidence = service._calculate_confidence(tools)

        assert confidence < 0.5

    def test_execute_tool_success(self, service, setup_data):
        """Should execute tool successfully."""
        result = service._execute_tool(
            "search_customer_pets",
            {"species": "dog", "customer_id": setup_data["customer"].id},
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["name"] == "Thor"

    def test_execute_tool_not_found(self, service):
        """Should handle unknown tool name."""
        result = service._execute_tool("unknown_tool", {})

        assert "error" in result

    def test_execute_tool_error(self, service):
        """Should handle tool execution errors."""
        result = service._execute_tool("search_customer_pets", {"age_min": "invalid"})

        assert isinstance(result, dict | list)
