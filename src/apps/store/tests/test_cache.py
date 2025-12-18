import pytest
from rest_framework import status

from .factories import BrandFactory, CategoryFactory


@pytest.mark.django_db
class TestCacheDecorators:
    """Test cache decorators on viewsets"""

    def test_category_list_uses_cache(self, authenticated_client):
        client, user = authenticated_client
        CategoryFactory.create_batch(3)
        url = "/api/v1/store/categories/"

        response1 = client.get(url)
        response2 = client.get(url)

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.json() == response2.json()

    def test_brand_list_uses_cache(self, authenticated_client):
        client, user = authenticated_client
        BrandFactory.create_batch(3)
        url = "/api/v1/store/brands/"

        response1 = client.get(url)
        response2 = client.get(url)

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.json() == response2.json()
