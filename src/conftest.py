import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from rest_framework.test import APIClient

from src.apps.accounts.factories import UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client():
    user = UserFactory(is_staff=True)
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def staff_user():
    user = UserFactory(is_staff=True, is_superuser=False)
    permissions = Permission.objects.filter(
        content_type__app_label__in=["store", "accounts", "pets", "schedule"],
        codename__startswith="view_",
    )
    user.user_permissions.add(*permissions)
    return user


@pytest.fixture
def superuser():
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def admin_client(superuser):
    client = Client()
    client.force_login(superuser)
    return client
