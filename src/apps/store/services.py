from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

import structlog
from django.db import transaction

from .models import ProductLot, Sale, SaleItem

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from django.db.models.query import QuerySet

    from src.apps.accounts.models import Customer
    from src.apps.store.models import Product


logger = structlog.get_logger(__name__)


class InsufficientStockError(Exception):
    """Custom exception for stock validation errors."""

    pass


class SaleService:
    @staticmethod
    @transaction.atomic
    def create_sale(
        *,
        user: "User",  # noqa: UP037
        items_data: list[dict[str, Any]],
        customer: "Customer" | None = None,  # noqa: UP037
        sale_instance: Sale | None = None,
    ) -> Sale:
        """
        Creates or updates a sale, processes items, updates stock, and calculates the total value.

        Args:
            user: The user processing the sale.
            items_data: A list of dictionaries, each containing 'lot' and 'quantity'.
            customer: The customer associated with the sale (optional).
            sale_instance: An existing sale instance to update (optional).

        Returns:
            The created or updated Sale instance.

        Raises:
            InsufficientStockError: If the requested quantity for any lot exceeds available stock.
        """
        if sale_instance is None:
            sale = Sale.objects.create(processed_by=user, customer=customer)
        else:
            sale = sale_instance

        total_sale_value = Decimal("0")
        items_to_create: list[SaleItem] = []
        lots_to_update: list[ProductLot] = []

        for item_data in items_data:
            lot: ProductLot = item_data["lot"]
            quantity: int = item_data["quantity"]

            if lot.quantity < quantity:
                error_message = (
                    f"Estoque insuficiente para o produto {lot.product.name} (Lote: {lot.lot_number}). "
                    f"Disponível: {lot.quantity}, Solicitado: {quantity}."
                )
                logger.error(
                    "sale_creation_failed",
                    reason="insufficient_stock",
                    user=user.username,
                    product_name=lot.product.name,
                    lot_number=lot.lot_number,
                    quantity_available=lot.quantity,
                    quantity_requested=quantity,
                )
                raise InsufficientStockError(error_message)

            unit_price: Decimal = item_data.get("unit_price") or lot.final_price
            total_sale_value += Decimal(unit_price) * quantity
            lot.quantity -= quantity
            lots_to_update.append(lot)

            sale_item = SaleItem(
                sale=sale, lot=lot, quantity=quantity, unit_price=unit_price
            )
            items_to_create.append(sale_item)

        if not sale.items.exists():
            SaleItem.objects.bulk_create(items_to_create)

        ProductLot.objects.bulk_update(lots_to_update, ["quantity"])

        sale.total_value = total_sale_value
        sale.save(update_fields=["total_value"])

        logger.info(
            "sale_created_successfully",
            sale_id=sale.id,
            total_value=float(sale.total_value),
            processed_by=user.username,
            customer_id=customer.id if customer else None,
        )

        return sale


class ProductService:
    @staticmethod
    def calculate_product_final_price(product: "Product") -> Decimal:  # noqa: UP037
        """
        Calculates the best final price for a product based on its lots with available stock.
        It considers the lowest price among all lots, factoring in promotions.

        Args:
            product: The Product instance to calculate the price for.

        Returns:
            The best final price for the product as a Decimal.
        """
        lots_with_stock: "QuerySet[ProductLot]" = product.lots.filter(  # noqa: UP037
            quantity__gt=0
        ).order_by("expiration_date")

        best_price: Decimal = product.price

        if not lots_with_stock.exists():
            return best_price

        for lot in lots_with_stock:
            if lot.final_price < best_price:
                best_price = lot.final_price

        if best_price == product.price:
            first_lot = lots_with_stock.first()
            if first_lot:
                return first_lot.final_price

        return best_price
