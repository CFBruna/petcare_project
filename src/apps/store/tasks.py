from celery import shared_task
from django.utils import timezone

from .models import ProductLot


@shared_task
def apply_expiration_discounts():
    today = timezone.now().date()
    lots_to_check = ProductLot.objects.filter(
        expiration_date__isnull=False, quantity__gt=0
    ).select_related("product")

    updated_count = 0
    for lot in lots_to_check:
        days_until_expiration = (lot.expiration_date - today).days
        new_discount = 0

        if 5 < days_until_expiration <= 14:
            new_discount = 50
        elif 14 < days_until_expiration <= 30:
            new_discount = 30
        elif 30 < days_until_expiration <= 60:
            new_discount = 20
        elif 60 < days_until_expiration <= 90:
            new_discount = 10
        elif 0 <= days_until_expiration <= 5:
            new_discount = 60

        if lot.auto_discount_percentage != new_discount:
            lot.auto_discount_percentage = new_discount
            lot.save(update_fields=["auto_discount_percentage"])
            updated_count += 1

    return f"{updated_count} lotes tiveram seu desconto por validade atualizado."
