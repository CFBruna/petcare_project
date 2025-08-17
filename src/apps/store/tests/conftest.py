import pytest
from rest_framework.test import APIClient

from src.apps.accounts.tests.factories import UserFactory


@pytest.fixture
def api_client():
    """
    Fixture for an unauthenticated API client.
    """
    return APIClient()


@pytest.fixture
def authenticated_client():
    """
    Fixture for an authenticated API client.
    Returns a tuple of (client, user).
    """
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user
