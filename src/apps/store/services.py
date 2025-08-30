from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction

from .models import Product, ProductLot, Sale, SaleItem


class InsufficientStockError(Exception):
    pass


@transaction.atomic
def create_sale(
    *, user: User, items_data: list[dict], customer=None, sale_instance: Sale = None
) -> Sale:
    if sale_instance is None:
        sale = Sale.objects.create(processed_by=user, customer=customer)
    else:
        sale = sale_instance

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

    if not sale.items.exists():
        SaleItem.objects.bulk_create(items_to_create)

    ProductLot.objects.bulk_update(lots_to_update, ["quantity"])

    sale.total_value = total_sale_value
    sale.save(update_fields=["total_value"])

    return sale


def calculate_product_final_price(product: Product) -> Decimal:
    lots_with_stock = product.lots.filter(quantity__gt=0).order_by("expiration_date")

    best_price = product.price

    if not lots_with_stock.exists():
        return best_price

    for lot in lots_with_stock:
        if lot.final_price < best_price:
            best_price = lot.final_price

    if best_price == product.price:
        return lots_with_stock.first().final_price

    return best_price
