from rest_framework import serializers


class DailyMetricSerializer(serializers.Serializer):
    """
    Serializer for daily metrics data.

    Represents aggregated data for a single day including revenue,
    appointments, and new customers.
    """

    date = serializers.DateField(help_text="Date of the metric")
    total_revenue = serializers.FloatField(help_text="Total revenue for the day in BRL")
    total_appointments = serializers.IntegerField(
        help_text="Number of appointments scheduled"
    )
    new_customers = serializers.IntegerField(
        help_text="Number of new customers registered"
    )


class AppointmentStatusDistributionSerializer(serializers.Serializer):
    """
    Serializer for appointment status distribution.

    Shows count of appointments by status for the selected period.
    """

    status = serializers.CharField(help_text="Appointment status")
    count = serializers.IntegerField(
        help_text="Number of appointments with this status"
    )


class TopProductSerializer(serializers.Serializer):
    """
    Serializer for top-selling products.

    Includes product details and sales performance metrics.
    """

    product_id = serializers.IntegerField(help_text="Product ID")
    product_name = serializers.CharField(help_text="Product name")
    category_name = serializers.CharField(help_text="Category name", allow_null=True)
    units_sold = serializers.IntegerField(help_text="Total units sold")
    revenue_generated = serializers.FloatField(
        help_text="Total revenue generated in BRL"
    )


class DashboardDataSerializer(serializers.Serializer):
    """
    Main serializer for dashboard analytics data.

    Aggregates all dashboard metrics in a single response:
    - Period information (start/end dates)
    - Daily metrics time series
    - Appointment status breakdown
    - Top products by revenue
    """

    period_start = serializers.DateField(
        help_text="Start date of the analysis period (ISO format)"
    )
    period_end = serializers.DateField(
        help_text="End date of the analysis period (ISO format)"
    )
    metrics_history = DailyMetricSerializer(
        many=True, help_text="Daily metrics for the period"
    )
    status_distribution = AppointmentStatusDistributionSerializer(
        many=True, help_text="Appointment status distribution"
    )
    top_products = TopProductSerializer(
        many=True, help_text="Top 5 products by revenue"
    )
