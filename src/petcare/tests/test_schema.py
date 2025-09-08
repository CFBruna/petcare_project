import pytest
from django.db import models
from rest_framework.viewsets import ModelViewSet

from src.petcare.schema import CustomAutoSchema


class MockModel(models.Model):
    objects = models.Manager()

    class Meta:
        app_label = "petcare"
        verbose_name = "Mock Object"
        verbose_name_plural = "Mock Objects"


class MockViewSet(ModelViewSet):
    queryset = MockModel.objects.all()  # type: ignore[misc]

    def _get_model_name(self, plural: bool = False) -> str:
        meta = self.queryset.model._meta
        name = meta.verbose_name_plural if plural else meta.verbose_name
        if not name:
            return ""
        return name.title()


@pytest.mark.parametrize(
    "action, expected_summary",
    [
        ("list", "List all Mock Objects"),
        ("retrieve", "Retrieve a Mock Object"),
        ("create", "Create a new Mock Object"),
        ("update", "Update a Mock Object"),
        ("partial_update", "Partially update a Mock Object"),
        ("destroy", "Delete a Mock Object"),
        ("some_other_action", None),
    ],
)
def test_custom_auto_schema_get_summary(action, expected_summary):
    """
    Tests if CustomAutoSchema generates the correct summary for each standard action.
    """
    view = MockViewSet()
    view.action = action

    schema = CustomAutoSchema()
    schema.view = view

    summary = schema.get_summary()

    assert summary == expected_summary
