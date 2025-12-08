from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from src.apps.accounts.models import Customer
from src.apps.schedule.models import Appointment
from src.apps.store.models import Sale, SaleItem


class AnalyticsService:
    """
    Service layer for analytics data aggregation.

    Provides optimized database queries for dashboard metrics,
    minimizing N+1 queries and database round-trips.
    """

    @staticmethod
    def get_dashboard_metrics(days: int = 7) -> dict:
        """
        Aggregates dashboard metrics for the specified period.

        Single service call returns all metrics needed for the dashboard,
        using optimized queries with annotate/aggregate.

        Args:
            days: Number of days to look back from today (default: 7)

        Returns:
            Dictionary containing:
            - period_start: ISO date string
            - period_end: ISO date string
            - metrics_history: List of daily metrics (revenue, appointments, customers)
            - status_distribution: List of appointment status counts
            - top_products: List of top 5 products by revenue
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days - 1)

        daily_metrics = (
            Sale.objects.filter(
                created_at__date__gte=start_date, created_at__date__lte=end_date
            )
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(total_revenue=Sum("total_value"), total_sales=Count("id"))
            .order_by("date")
        )

        new_customers_per_day = (
            Customer.objects.filter(
                user__date_joined__date__gte=start_date,
                user__date_joined__date__lte=end_date,
            )
            .annotate(date=TruncDate("user__date_joined"))
            .values("date")
            .annotate(new_customers=Count("id"))
            .order_by("date")
        )

        appointments_per_day = (
            Appointment.objects.filter(
                schedule_time__date__gte=start_date, schedule_time__date__lte=end_date
            )
            .annotate(date=TruncDate("schedule_time"))
            .values("date")
            .annotate(total_appointments=Count("id"))
            .order_by("date")
        )

        daily_data_map = {}
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            daily_data_map[current_date] = {
                "date": current_date.isoformat(),
                "total_revenue": Decimal("0.00"),
                "total_appointments": 0,
                "new_customers": 0,
            }

        for metric in daily_metrics:
            date_key = metric["date"]
            if date_key in daily_data_map:
                daily_data_map[date_key]["total_revenue"] = float(
                    metric["total_revenue"] or 0
                )

        for metric in new_customers_per_day:
            date_key = metric["date"]
            if date_key in daily_data_map:
                daily_data_map[date_key]["new_customers"] = metric["new_customers"]

        for metric in appointments_per_day:
            date_key = metric["date"]
            if date_key in daily_data_map:
                daily_data_map[date_key]["total_appointments"] = metric[
                    "total_appointments"
                ]

        status_distribution = list(
            Appointment.objects.filter(
                schedule_time__date__gte=start_date, schedule_time__date__lte=end_date
            )
            .values("status")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        top_products = list(
            SaleItem.objects.filter(
                sale__created_at__date__gte=start_date,
                sale__created_at__date__lte=end_date,
            )
            .select_related("lot__product", "lot__product__category")
            .values(
                product_id=F("lot__product__id"),
                product_name=F("lot__product__name"),
                category_name=F("lot__product__category__name"),
            )
            .annotate(
                units_sold=Sum("quantity"),
                revenue_generated=Sum(F("quantity") * F("unit_price")),
            )
            .order_by("-revenue_generated")[:5]
        )

        metrics_history = [daily_data_map[d] for d in sorted(daily_data_map.keys())]

        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "metrics_history": metrics_history,
            "status_distribution": status_distribution,
            "top_products": top_products,
        }
