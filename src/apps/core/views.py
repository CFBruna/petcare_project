from django.http import JsonResponse
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


class HealthCheckView(View):
    """
    A simple view that returns a 200 OK status if the service is running.
    Used by the deployment script to verify application health.
    """

    def get(self, request, *args, **kwargs):
        return JsonResponse({"status": "ok", "service": "petcare"})
