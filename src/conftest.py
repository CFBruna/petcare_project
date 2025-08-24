import pytest
from rest_framework.test import APIClient

from src.apps.accounts.tests.factories import UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client():
    user = UserFactory()

    user.is_staff = True
    user.save()

    client = APIClient()
    client.force_authenticate(user=user)
    return client, user
