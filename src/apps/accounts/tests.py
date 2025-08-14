import pytest
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_user_creation():
    User.objects.create_user(username="testuser", password="password123")
    assert User.objects.count() == 1
