from dataclasses import dataclass
from typing import Any

import structlog
from django.conf import settings
from django.utils import timezone
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langchain_google_genai import ChatGoogleGenerativeAI

from src.apps.ai.agents.tools import (
    CalculatePriceTool,
    CheckAvailabilityTool,
    SearchCustomerPetsTool,
    calculate_price,
    check_availability,
    search_customer_pets,
)
from src.apps.ai.prompts import scheduling_prompts
from src.apps.ai.services import retry_on_rate_limit

logger = structlog.get_logger(__name__)


@dataclass
class ToolExecution:
    """Record of a tool execution during agent run."""

    tool_name: str
    arguments: dict[str, Any]
    result: Any
    thinking: str = ""


@dataclass
class SchedulingIntentRequest:
    """Request to generate scheduling intent from natural language."""

    user_input: str
    customer_id: int | None = None


@dataclass
class SchedulingIntentResponse:
    """Response from scheduling agent."""

    message: str
    tools_executed: list[ToolExecution]
    intent_detected: str
    confidence_score: float


class SchedulingAgentService:
    """Service for AI-powered scheduling with Gemini Function Calling.

    Responsibilities:
    - Interpret natural language booking requests
    - Execute appropriate tools (search, availability, pricing)
    - Generate human-friendly responses
    - Track tool execution for transparency
    """

    def __init__(self):
        """Initialize LLM and bind tools."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL_NAME,
            temperature=0.3,
            google_api_key=settings.GOOGLE_API_KEY,
        )

        self.tools = [
            StructuredTool.from_function(
                func=search_customer_pets,
                name="search_customer_pets",
                description=SearchCustomerPetsTool.__doc__ or "Search for pets",
                args_schema=SearchCustomerPetsTool,
            ),
            StructuredTool.from_function(
                func=check_availability,
                name="check_availability",
                description=CheckAvailabilityTool.__doc__ or "Check availability",
                args_schema=CheckAvailabilityTool,
            ),
            StructuredTool.from_function(
                func=calculate_price,
                name="calculate_price",
                description=CalculatePriceTool.__doc__ or "Calculate price",
                args_schema=CalculatePriceTool,
            ),
        ]

        self.llm_with_tools = self.llm.bind_tools(self.tools)

    @retry_on_rate_limit(max_retries=3, base_delay=2)
    def generate_intent(
        self, request: SchedulingIntentRequest
    ) -> SchedulingIntentResponse:
        """Generate scheduling intent from natural language.

        This method orchestrates the agent interaction:
        1. Send user request to LLM with tools
        2. Execute any tool calls requested by LLM
        3. Send results back to LLM
        4. Get final natural language response

        Args:
            request: User's natural language request

        Returns:
            Structured response with message and tool execution trace
        """
        logger.info(
            "generate_intent_started",
            user_input=request.user_input,
            customer_id=request.customer_id,
        )

        tools_executed: list[ToolExecution] = []

        current_date = timezone.now().strftime("%d/%m/%Y")
        messages = [
            SystemMessage(content=scheduling_prompts.SCHEDULING_AGENT_SYSTEM),
            HumanMessage(
                content=scheduling_prompts.SCHEDULING_AGENT_USER_TEMPLATE.format(
                    user_input=request.user_input,
                    current_date=current_date,
                    customer_id=request.customer_id or "not provided",
                )
            ),
        ]

        response = self.llm_with_tools.invoke(messages)
        messages.append(response)

        if hasattr(response, "tool_calls") and response.tool_calls:
            logger.info("tool_calls_requested", count=len(response.tool_calls))

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                logger.info(
                    "executing_tool",
                    tool_name=tool_name,
                    arguments=tool_args,
                )

                tool_result = self._execute_tool(tool_name, tool_args)

                tools_executed.append(
                    ToolExecution(
                        tool_name=tool_name,
                        arguments=tool_args,
                        result=tool_result,
                        thinking=f"Executing {tool_name}...",
                    )
                )

                from langchain_core.messages import ToolMessage

                messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"],
                    )
                )

            final_response = self.llm.invoke(messages)
            final_message = final_response.content
        else:
            final_message = response.content

        intent = self._detect_intent(request.user_input, tools_executed)

        confidence = self._calculate_confidence(tools_executed)

        logger.info(
            "generate_intent_completed",
            intent=intent,
            confidence=confidence,
            tools_used=len(tools_executed),
        )

        return SchedulingIntentResponse(
            message=final_message,
            tools_executed=tools_executed,
            intent_detected=intent,
            confidence_score=confidence,
        )

    def _execute_tool(self, tool_name: str, arguments: dict) -> Any:
        """Execute a tool by name with given arguments."""
        from collections.abc import Callable

        tool_map: dict[str, Callable[..., Any]] = {
            "search_customer_pets": search_customer_pets,
            "check_availability": check_availability,
            "calculate_price": calculate_price,
        }

        tool_func = tool_map.get(tool_name)
        if not tool_func:
            logger.error("tool_not_found", tool_name=tool_name)
            return {"error": f"Tool {tool_name} not found"}

        try:
            return tool_func(**arguments)
        except Exception as e:
            logger.error(
                "tool_execution_failed",
                tool_name=tool_name,
                error=str(e),
            )
            return {"error": str(e)}

    def _detect_intent(
        self, user_input: str, tools_executed: list[ToolExecution]
    ) -> str:
        """Detect the user's intent based on input and tools used."""
        user_lower = user_input.lower()

        booking_keywords = [
            "agendar",
            "marcar",
            "preciso",
            "quero",
            "reservar",
            "consulta",
        ]
        if any(keyword in user_lower for keyword in booking_keywords):
            return "book_appointment"

        if any(t.tool_name == "check_availability" for t in tools_executed):
            return "check_availability"

        return "unknown"

    def _calculate_confidence(self, tools_executed: list[ToolExecution]) -> float:
        """Calculate confidence score based on tool execution success."""
        if not tools_executed:
            return 0.5

        successful_tools = sum(
            1
            for t in tools_executed
            if not isinstance(t.result, dict) or "error" not in t.result
        )

        confidence = successful_tools / len(tools_executed)

        tool_names = {t.tool_name for t in tools_executed}
        if "search_customer_pets" in tool_names and "check_availability" in tool_names:
            confidence = min(1.0, confidence + 0.2)

        return round(confidence, 2)
