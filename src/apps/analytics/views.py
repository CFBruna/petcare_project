from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.analytics.serializers import DashboardDataSerializer
from src.apps.analytics.services import AnalyticsService


class DashboardMetricsView(APIView):
    """
    API endpoint for dashboard analytics metrics.

    Returns aggregated metrics for the specified period including:
    - Daily revenue and appointment trends
    - Appointment status distribution
    - Top-selling products

    Query Parameters:
    - days (int): Number of days to look back (default: 7, max: 90)
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Dashboard Metrics",
        description="Retrieves aggregated analytics data for the dashboard including revenue trends, appointments, and top products",
        parameters=[
            OpenApiParameter(
                name="days",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of days to analyze (default: 7, max: 90)",
                required=False,
            )
        ],
        responses={200: DashboardDataSerializer},
        tags=["Analytics"],
    )
    def get(self, request):
        """
        Handle GET request for dashboard metrics.

        Validates 'days' parameter and delegates to AnalyticsService.
        """
        days_param = request.query_params.get("days", "7")

        try:
            days = int(days_param)
        except ValueError:
            return Response(
                {"error": "Parameter 'days' must be an integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if days < 1:
            return Response(
                {"error": "Parameter 'days' must be at least 1"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if days > 90:
            return Response(
                {"error": "Parameter 'days' cannot exceed 90"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = AnalyticsService.get_dashboard_metrics(days=days)
        except Exception as e:
            return Response(
                {"error": "Failed to retrieve metrics", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = DashboardDataSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
