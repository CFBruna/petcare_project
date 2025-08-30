from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction

from .models import ProductLot, Sale, SaleItem


class InsufficientStockError(Exception):
    pass


@transaction.atomic
def create_sale(*, user: User, items_data: list[dict], customer=None) -> Sale:
    sale = Sale.objects.create(processed_by=user, customer=customer)
    total_sale_value = Decimal("0")
    items_to_create = []
    lots_to_update = []

    for item_data in items_data:
        lot = item_data["lot"]
        quantity = item_data["quantity"]

        if lot.quantity < quantity:
            raise InsufficientStockError(
                f"Estoque insuficiente para o produto {lot.product.name} (Lote: {lot.lot_number}). "
                f"Disponível: {lot.quantity}, Solicitado: {quantity}."
            )

        unit_price = item_data.get("unit_price") or lot.final_price
        total_sale_value += unit_price * quantity
        lot.quantity -= quantity
        lots_to_update.append(lot)

        sale_item = SaleItem(
            sale=sale, lot=lot, quantity=quantity, unit_price=unit_price
        )
        items_to_create.append(sale_item)

    SaleItem.objects.bulk_create(items_to_create)
    ProductLot.objects.bulk_update(lots_to_update, ["quantity"])

    sale.total_value = total_sale_value
    sale.save(update_fields=["total_value"])

    return sale
