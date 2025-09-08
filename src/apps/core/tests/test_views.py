import pytest
from django.db import models

from src.apps.core.views import AutoSchemaModelNameMixin


class DummyModel(models.Model):
    objects = models.Manager()

    class Meta:
        app_label = "core"
        verbose_name = "Dummy"
        verbose_name_plural = "Dummies"


class DummyViewSet(AutoSchemaModelNameMixin):
    queryset = DummyModel.objects.all()  # type: ignore[misc]


@pytest.mark.django_db
class TestAutoSchemaModelNameMixin:
    def test_get_model_name_singular(self):
        mixin = DummyViewSet()
        assert mixin._get_model_name() == "Dummy"

    def test_get_model_name_plural(self):
        mixin = DummyViewSet()
        assert mixin._get_model_name(plural=True) == "Dummies"

    def test_get_model_name_no_queryset_returns_empty(self):
        class NoQuerySetViewSet(AutoSchemaModelNameMixin):
            queryset = None

        mixin = NoQuerySetViewSet()
        assert mixin._get_model_name() == ""
