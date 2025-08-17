import pytest

from src.apps.health.models import HealthRecord
from src.apps.health.tests.factories import HealthRecordFactory


@pytest.mark.django_db
class TestHealthRecordModel:
    def test_health_record_str_representation(self):
        record = HealthRecordFactory(
            pet__name="Malu", record_type=HealthRecord.RecordType.VACCINE
        )
        assert str(record) == "Vacina de Malu"
