import os

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic import TemplateView


class AutoSchemaModelNameMixin:
    """
    A helper mixin that provides a method to get the model's verbose name.
    This is used by the CustomAutoSchema to generate dynamic summaries.
    """

    def _get_model_name(self, plural: bool = False) -> str:
        if not hasattr(self, "queryset") or self.queryset is None:
            return ""

        model = self.queryset.model
        meta = model._meta
        name = meta.verbose_name_plural if plural else meta.verbose_name
        return name.title()


class LandingPageView(TemplateView):
    template_name = "core/landing_page.html"


class DashboardView(View):
    """
    Serves the TypeScript/React analytics dashboard frontend.
    Reads the Vite-built index.html and serves it directly.
    """

    def get(self, request):
        dashboard_path = os.path.join(
            settings.BASE_DIR, "src", "static", "dashboard", "index.html"
        )

        try:
            with open(dashboard_path, encoding="utf-8") as f:
                html_content = f.read()
            return HttpResponse(html_content, content_type="text/html")
        except FileNotFoundError:
            return HttpResponse(
                "<h1>Dashboard not built</h1>"
                "<p>Run: <code>cd frontend && npm run build</code></p>",
                status=404,
            )


class HealthCheckView(View):
    """
    A simple view that returns a 200 OK status if the service is running.
    Used by the deployment script to verify application health.
    """

    def get(self, request, *args, **kwargs):
        return JsonResponse({"status": "ok", "service": "petcare"})
