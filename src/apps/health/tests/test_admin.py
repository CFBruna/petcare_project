import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from src.apps.accounts.tests.factories import UserFactory
from src.apps.health.admin import HealthRecordAdmin
from src.apps.health.models import HealthRecord
from src.apps.health.tests.factories import HealthRecordFactory
from src.apps.pets.tests.factories import PetFactory


@pytest.mark.django_db
class TestHealthRecordAdmin:
    def setup_method(self):
        self.site = AdminSite()
        self.admin = HealthRecordAdmin(HealthRecord, self.site)
        self.factory = RequestFactory()
        self.user = UserFactory()

    def test_save_model_sets_created_by(self):
        pet = PetFactory()
        record = HealthRecord(
            pet=pet,
            record_type=HealthRecord.RecordType.NOTE,
            record_date="2025-01-01",
        )
        request = self.factory.get("/")
        request.user = self.user

        self.admin.save_model(request, record, None, None)

        assert record.created_by == self.user

    def test_save_model_does_not_change_created_by_on_update(self):
        another_user = UserFactory()
        record = HealthRecordFactory(created_by=another_user)
        request = self.factory.get("/")
        request.user = self.user

        self.admin.save_model(request, record, None, True)
        record.refresh_from_db()

        assert record.created_by == another_user
