from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.utils import timezone

from .factories import (
    BrandFactory,
    CategoryFactory,
    ProductFactory,
    ProductLotFactory,
    PromotionFactory,
    PromotionRuleFactory,
    SaleFactory,
    SaleItemFactory,
)


@pytest.mark.django_db
class TestStoreModels:
    def test_category_str(self):
        category = CategoryFactory(name="Brinquedos")
        assert str(category) == "Brinquedos"

    def test_brand_str(self):
        brand = BrandFactory(name="PetSafe")
        assert str(brand) == "PetSafe"

    def test_product_str(self):
        product = ProductFactory(name="Bolinha de Borracha")
        assert str(product) == "Bolinha de Borracha"

    def test_product_has_brand_and_category(self):
        product = ProductFactory()
        assert product.brand is not None
        assert product.category is not None
        assert product.brand.name.startswith("Marca")
        assert product.category.name.startswith("Categoria")

    def test_deleting_category_with_product_fails(self):
        product = ProductFactory()
        category = product.category
        with pytest.raises(ProtectedError):
            category.delete()

    def test_deleting_brand_with_product_fails(self):
        product = ProductFactory()
        brand = product.brand
        with pytest.raises(ProtectedError):
            brand.delete()


@pytest.mark.django_db
class TestSaleModels:
    def test_sale_str_representation(self):
        sale = SaleFactory()
        expected_str = f"Venda #{sale.id} - {sale.created_at.strftime('%d/%m/%Y')}"
        assert str(sale) == expected_str

    def test_sale_item_str_representation(self):
        lot = ProductLotFactory(lot_number="A123", product__name="Ração Premium")
        sale_item = SaleItemFactory(lot=lot, quantity=3)
        assert str(sale_item) == "3x Ração Premium (Lote: A123)"


@pytest.mark.django_db
class TestProductInventoryModel:
    def test_total_stock_is_calculated_from_lots(self):
        product = ProductFactory()
        ProductLotFactory(product=product, quantity=10)
        ProductLotFactory(product=product, quantity=15)
        assert product.total_stock == 25

    def test_final_price_is_normal_price_without_promotion(self):
        product = ProductFactory(price=100.00)
        ProductLotFactory(product=product, quantity=10)
        assert product.final_price == Decimal("100.00")

    def test_final_price_reflects_active_promotion(self):
        product = ProductFactory(price=Decimal("100.00"))
        lot = ProductLotFactory(product=product, quantity=10)
        now = timezone.now()
        promotion = PromotionFactory(
            start_date=now - timezone.timedelta(days=1),
            end_date=now + timezone.timedelta(days=1),
        )
        PromotionRuleFactory(
            promotion=promotion,
            lot=lot,
            discount_percentage=Decimal("20.00"),
            promotional_stock=5,
        )
        assert product.final_price == Decimal("80.00")
        assert lot.final_price == Decimal("80.00")

    def test_final_price_is_normal_price_with_expired_promotion(self):
        product = ProductFactory(price=Decimal("100.00"))
        lot = ProductLotFactory(product=product, quantity=10)
        now = timezone.now()
        promotion = PromotionFactory(
            start_date=now - timezone.timedelta(days=10),
            end_date=now - timezone.timedelta(days=1),
        )
        PromotionRuleFactory(
            promotion=promotion,
            lot=lot,
            discount_percentage=Decimal("20.00"),
            promotional_stock=5,
        )
        assert product.final_price == Decimal("100.00")
        assert lot.final_price == Decimal("100.00")

    def test_promotion_rule_validation(self):
        lot = ProductLotFactory(quantity=10)
        promotion = PromotionFactory()
        with pytest.raises(ValidationError):
            rule = PromotionRuleFactory.build(
                promotion=promotion, lot=lot, promotional_stock=15
            )
            rule.full_clean()

    def test_final_price_uses_highest_discount_between_manual_and_auto(self):
        product = ProductFactory(price=Decimal("100.00"))
        lot = ProductLotFactory(product=product, quantity=10)

        now = timezone.now()
        promotion = PromotionFactory(
            start_date=now - timezone.timedelta(days=1),
            end_date=now + timezone.timedelta(days=1),
        )
        PromotionRuleFactory(
            promotion=promotion, lot=lot, discount_percentage=Decimal("20.00")
        )

        lot.auto_discount_percentage = Decimal("50.00")
        lot.save()

        assert lot.final_price == Decimal("50.00")

        manual_promo_rule = lot.promotional_rules.first()
        manual_promo_rule.discount_percentage = Decimal("70.00")
        manual_promo_rule.save()

        assert lot.final_price == Decimal("30.00")
