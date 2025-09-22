import pytest
from django.urls import reverse

from src.apps.schedule.tests.factories import AppointmentFactory
from src.apps.store.tests.factories import (
    ProductLotFactory,
    PromotionFactory,
    SaleFactory,
)


@pytest.mark.django_db
class TestPetCareAdminSite:
    def test_dashboard_index_view(self, admin_client):
        """
        Tests if the custom admin index view (dashboard) loads correctly.
        """
        SaleFactory()
        AppointmentFactory()

        url = reverse("petcare_admin:index")
        response = admin_client.get(url)

        assert response.status_code == 200
        assert "Faturamento de Hoje" in str(response.content)

    def test_get_app_list_customization(self, admin_client):
        """
        Tests if the app list is correctly customized and ordered.
        """

        PromotionFactory()
        ProductLotFactory(auto_discount_percentage=10)

        url = reverse("petcare_admin:index")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")

        assert "Vendas e Estoque" in content
        assert "Agendamentos" in content
        assert "Cadastros Gerais" in content
        assert "Marketing e Promoções" in content
        assert "Administração do Sistema" in content
