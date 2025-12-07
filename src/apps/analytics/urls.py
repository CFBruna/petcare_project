from django.urls import path

from src.apps.analytics.views import DashboardMetricsView

app_name = "analytics"

urlpatterns = [
    path("dashboard/", DashboardMetricsView.as_view(), name="dashboard-metrics"),
]
