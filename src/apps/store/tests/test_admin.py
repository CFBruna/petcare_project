from typing import Any

import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse
from rest_framework import status

from src.apps.store.admin import AutoPromotionAdmin, SaleAdmin
from src.apps.store.models import AutoPromotion, ProductLot, Sale, SaleItem
from src.apps.store.tests.factories import (
    ProductLotFactory,
    SaleFactory,
    SaleItemFactory,
)


@pytest.mark.django_db
class TestSaleAdmin:
    def setup_method(self) -> None:
        self.site = AdminSite()
        self.admin = SaleAdmin(Sale, self.site)

    def test_display_sold_items_in_changelist(self, admin_client: Any) -> None:
        sale: Sale = SaleFactory()  # type: ignore[assignment]
        item1: SaleItem = SaleItemFactory(sale=sale, quantity=2)  # type: ignore[assignment]
        item2: SaleItem = SaleItemFactory(sale=sale, quantity=1)  # type: ignore[assignment]
        changelist_url = reverse("petcare_admin:store_sale_changelist")
        response = admin_client.get(changelist_url)
        assert response.status_code == status.HTTP_200_OK
        content = response.content.decode("utf-8")
        assert f"{item1.quantity}x {item1.product.name}" in content
        assert f"{item2.quantity}x {item2.product.name}" in content

    def test_display_sold_items_with_more_than_max_items(
        self, admin_client: Any
    ) -> None:
        sale: Sale = SaleFactory()  # type: ignore[assignment]
        SaleItemFactory.create_batch(4, sale=sale)
        changelist_url = reverse("petcare_admin:store_sale_changelist")
        response = admin_client.get(changelist_url)
        assert response.status_code == status.HTTP_200_OK
        assert "..." in response.content.decode("utf-8")

    def test_display_sold_items_no_items(self, admin_client: Any) -> None:
        SaleFactory()
        changelist_url = reverse("petcare_admin:store_sale_changelist")
        response = admin_client.get(changelist_url)
        assert "—" in response.content.decode("utf-8")

    def test_formset_is_invalid_on_insufficient_stock(self, admin_client: Any) -> None:
        lot: ProductLot = ProductLotFactory(quantity=5)  # type: ignore[assignment]
        add_url = reverse("petcare_admin:store_sale_add")
        form_data = {
            "customer": "",
            "items-TOTAL_FORMS": "1",
            "items-INITIAL_FORMS": "0",
            "items-MAX_NUM_FORMS": "1000",
            "items-0-lot": str(lot.id),
            "items-0-quantity": "10",
            "items-0-id": "",
            "items-0-DELETE": "",
            "_save": "Salvar",
        }

        response = admin_client.post(add_url, data=form_data)
        formset_in_context = response.context["inline_admin_formsets"][0].formset

        assert response.status_code == 200
        assert not formset_in_context.is_valid()
        assert any(
            "Estoque insuficiente" in error
            for error in formset_in_context.non_form_errors()
        )
        assert Sale.objects.count() == 0

    def test_change_view_is_forbidden_for_staff_user(
        self, client: Any, staff_user: Any
    ) -> None:
        client.force_login(staff_user)
        sale: Sale = SaleFactory()  # type: ignore[assignment]
        change_url = reverse("petcare_admin:store_sale_change", args=[sale.id])
        response = client.get(change_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_change_view_is_forbidden_for_superuser_as_well(
        self, admin_client: Any
    ) -> None:
        sale: Sale = SaleFactory()  # type: ignore[assignment]
        change_url = reverse("petcare_admin:store_sale_change", args=[sale.id])
        response = admin_client.get(change_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestProductLotAdmin:
    def test_search_results_filter_out_of_stock(self, admin_client: Any) -> None:
        ProductLotFactory(quantity=10, product__name="Available Product")
        ProductLotFactory(quantity=0, product__name="Out of Stock Product")
        changelist_url = reverse("petcare_admin:store_productlot_changelist")
        response = admin_client.get(changelist_url, {"q": "Product"})
        assert response.status_code == 200
        assert "Available Product" in str(response.content)
        assert "Out of Stock Product" not in str(response.content)


@pytest.mark.django_db
class TestAutoPromotionAdmin:
    def setup_method(self) -> None:
        self.site = AdminSite()
        self.admin = AutoPromotionAdmin(AutoPromotion, self.site)

    def test_auto_promotion_admin_permissions(self, rf: Any) -> None:
        request = rf.get("/")
        assert not self.admin.has_add_permission(request)
        assert not self.admin.has_change_permission(request, obj=ProductLotFactory())
        assert not self.admin.has_delete_permission(request, obj=ProductLotFactory())

    def test_price_with_discount_display(self) -> None:
        lot: ProductLot = ProductLotFactory(  # type: ignore[assignment]
            product__price=100, auto_discount_percentage=20
        )
        display_html = self.admin.price_with_discount(lot)
        assert 'style="text-decoration: line-through;">R$ 100.00</span>' in display_html
        assert 'style="color: #4CAF50;">R$ 80.00 (-20%)</strong>' in display_html


# Fix the patch path - service is imported inside the admin action function


@pytest.mark.django_db
class TestProductAdminActions:
    """Test ProductAdmin AI description actions."""

    def test_generate_technical_description(self, admin_client: Any) -> None:
        """Should generate technical descriptions."""
        from unittest.mock import MagicMock, patch

        from src.apps.ai.services import ProductDescriptionResponse
        from src.apps.store.tests.factories import ProductFactory
        from src.apps.store.models import Product

        product: Product = ProductFactory(name="Test Product")  # type: ignore[assignment]

        # Patch where it's imported (inside the function)
        with patch("src.apps.ai.services.ProductIntelligenceService") as MockService:
            mock_service = MagicMock()
            MockService.return_value = mock_service
            mock_service.generate_description.return_value = ProductDescriptionResponse(
                description="AI generated description",
                confidence_score=0.9,
                is_known_product=True,
                similar_products=[],
                suggestions={},
            )

            changelist_url = reverse("petcare_admin:store_product_changelist")
            response = admin_client.post(
                changelist_url,
                {
                    "action": "generate_technical_description",
                    "_selected_action": [str(product.id)],
                },
                follow=True,
            )

            assert response.status_code == 200
            product.refresh_from_db()
            assert product.description == "AI generated description"

    def test_generate_creative_description(self, admin_client: Any) -> None:
        """Should generate creative descriptions."""
        from unittest.mock import MagicMock, patch

        from src.apps.ai.services import ProductDescriptionResponse
        from src.apps.store.tests.factories import ProductFactory
        from src.apps.store.models import Product

        product: Product = ProductFactory(name="Test Product")  # type: ignore[assignment]

        with patch("src.apps.ai.services.ProductIntelligenceService") as MockService:
            mock_service = MagicMock()
            MockService.return_value = mock_service
            mock_service.generate_description.return_value = ProductDescriptionResponse(
                description="Creative AI description",
                confidence_score=0.8,
                is_known_product=False,
                similar_products=[],
                suggestions={},
            )

            changelist_url = reverse("petcare_admin:store_product_changelist")
            response = admin_client.post(
                changelist_url,
                {
                    "action": "generate_creative_description",
                    "_selected_action": [str(product.id)],
                },
                follow=True,
            )

            assert response.status_code == 200
