#!/usr/bin/env python
"""Demo script for Scheduling Agent - Interactive testing.

Run with:
    docker compose exec web python scripts/demo_scheduling_agent.py
"""

# ruff: noqa: E402, I001
# Django setup must happen before model imports

import os
import sys

import django

# Setup Django before imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.petcare.settings")
django.setup()

from src.apps.ai.agents.scheduling_agent import (
    SchedulingAgentService,
    SchedulingIntentRequest,
)


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_tool_execution(tool):
    """Print tool execution details."""
    print(f"🔧 Tool: {tool.tool_name}")
    print(f"   Arguments: {tool.arguments}")
    print(f"   Result: {tool.result}")
    print()


def demo_complete_booking_flow():
    """Demo 1: Complete booking flow with all tools."""
    print_header("Demo 1: Complete Booking Flow")

    service = SchedulingAgentService()
    request = SchedulingIntentRequest(
        user_input="Preciso banho e tosa para meu Golden Retriever de 5 anos, de preferência sábado de manhã",
        customer_id=1,
    )

    print(f"📝 User Input: {request.user_input}\n")

    result = service.generate_intent(request)

    print(f"💬 Agent Response:\n{result.message}\n")
    print(f"🎯 Intent Detected: {result.intent_detected}")
    print(f"📊 Confidence Score: {result.confidence_score}\n")

    print(f"🔧 Tools Executed ({len(result.tools_executed)}):")
    for tool in result.tools_executed:
        print_tool_execution(tool)


def demo_availability_check():
    """Demo 2: Simple availability check."""
    print_header("Demo 2: Availability Check")

    service = SchedulingAgentService()
    request = SchedulingIntentRequest(
        user_input="Quais horários disponíveis no sábado?",
    )

    print(f"📝 User Input: {request.user_input}\n")

    result = service.generate_intent(request)

    print(f"💬 Agent Response:\n{result.message}\n")
    print(f"📊 Confidence: {result.confidence_score}")


def demo_error_handling():
    """Demo 3: Error handling - pet not found."""
    print_header("Demo 3: Error Handling")

    service = SchedulingAgentService()
    request = SchedulingIntentRequest(
        user_input="Agendar consulta para meu dinossauro de estimação",
    )

    print(f"📝 User Input: {request.user_input}\n")

    result = service.generate_intent(request)

    print(f"💬 Agent Response:\n{result.message}\n")
    print(f"🎯 Intent: {result.intent_detected}")
    print(f"📊 Confidence: {result.confidence_score}")


def main():
    """Run all demos."""
    print("\n")
    print("🤖 SCHEDULING AGENT - INTERACTIVE DEMO")
    print("=" * 80)

    try:
        demo_complete_booking_flow()
        demo_availability_check()
        demo_error_handling()

        print_header("✅ Demo Complete!")
        print("Next steps:")
        print(
            "  1. Test via Swagger UI: http://localhost:8000/api/v1/schema/swagger-ui/"
        )
        print("  2. Check endpoint: POST /api/v1/ai/schedule-intent/")
        print("  3. Try different inputs in Portuguese!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  - GOOGLE_API_KEY is set in .env")
        print("  - Database has sample data (run: python manage.py seed_db)")
        print("  - Containers are running (docker compose up)")


if __name__ == "__main__":
    main()
