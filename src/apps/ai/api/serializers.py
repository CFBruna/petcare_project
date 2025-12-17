from rest_framework import serializers


class ToolExecutionSerializer(serializers.Serializer):
    """Serializer for tool execution record."""

    tool_name = serializers.CharField()
    arguments = serializers.DictField()
    result = serializers.JSONField()
    thinking = serializers.CharField(required=False, allow_blank=True)


class SchedulingIntentRequestSerializer(serializers.Serializer):
    """Serializer for scheduling intent request."""

    user_input = serializers.CharField(
        max_length=1000,
        help_text="Natural language scheduling request in Portuguese",
    )
    customer_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Optional customer ID to filter pets",
    )


class SchedulingIntentResponseSerializer(serializers.Serializer):
    """Serializer for scheduling intent response."""

    message = serializers.CharField(help_text="Natural language response to the user")
    tools_executed = ToolExecutionSerializer(
        many=True, help_text="List of tools executed during processing"
    )
    intent_detected = serializers.ChoiceField(
        choices=[
            ("book_appointment", "Book Appointment"),
            ("check_availability", "Check Availability"),
            ("unknown", "Unknown"),
        ],
        help_text="Detected user intent",
    )
    confidence_score = serializers.FloatField(
        help_text="Confidence score (0.0 - 1.0)",
    )
