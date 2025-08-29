from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Sum
from django.utils import timezone

from .models import ProductLot, Promotion, Sale


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


@shared_task
def generate_daily_sales_report():
    today = timezone.localdate()
    yesterday = today - timezone.timedelta(days=1)

    sales = (
        Sale.objects.filter(created_at__date=yesterday)
        .prefetch_related("items__lot__product")
        .order_by("created_at")
    )
    total_revenue = sales.aggregate(total=Sum("total_value"))["total"] or 0

    subject = f"Relatório Diário de Vendas - {yesterday.strftime('%d/%m/%Y')}"

    if not sales.exists():
        message = "Nenhuma venda foi registrada nesta data."
    else:
        subject += f" ({sales.count()} vendas)"
        report_lines = [
            f"Relatório de vendas de {yesterday.strftime('%d/%m/%Y')}:",
            "=" * 40,
        ]

        for sale in sales:
            sale_time = timezone.localtime(sale.created_at).strftime("%H:%M")
            report_lines.append(
                f"\nVenda #{sale.id} - {sale_time}h - Total: R$ {sale.total_value:.2f}"
            )
            for item in sale.items.all():
                report_lines.append(
                    f"  - {item.quantity}x {item.lot.product.name} @ R$ {item.unit_price:.2f}"
                )

        report_lines.append("\n" + "=" * 40)
        report_lines.append(f"Faturamento Total do Dia: R$ {total_revenue:.2f}")

        message = "\n".join(report_lines)

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.ADMIN_EMAIL],
        fail_silently=False,
    )

    return f"Relatório de vendas para {yesterday.strftime('%d/%m/%Y')} enviado com sucesso."


@shared_task
def generate_daily_promotions_report():
    today = timezone.localdate()
    yesterday = today - timezone.timedelta(days=1)

    newly_promoted_lots = ProductLot.objects.filter(
        auto_discount_percentage__gt=0
    ).extra(
        where=[f"DATE(updated_at AT TIME ZONE '{settings.TIME_ZONE}') = %s"],
        params=[yesterday],
    )

    newly_unpromoted_lots = ProductLot.objects.filter(auto_discount_percentage=0).extra(
        where=[f"DATE(updated_at AT TIME ZONE '{settings.TIME_ZONE}') = %s"],
        params=[yesterday],
    )

    active_manual_promotions = Promotion.objects.active().prefetch_related(
        "rules__lot__product"
    )
    active_auto_promotions = ProductLot.objects.filter(
        auto_discount_percentage__gt=0, quantity__gt=0
    ).select_related("product")

    subject = f"Relatório Diário de Promoções - {today.strftime('%d/%m/%Y')}"
    report_lines = [
        f"Relatório de status das promoções em {today.strftime('%d/%m/%Y')}:",
        "=" * 50,
    ]

    report_lines.append("\n== MUDANÇAS NAS PROMOÇÕES AUTOMÁTICAS (ONTEM) ==\n")
    if newly_promoted_lots.exists():
        report_lines.append("Produtos que ENTRARAM em promoção por validade:")
        for lot in newly_promoted_lots:
            report_lines.append(
                f"  - {lot.product.name} (Lote: {lot.lot_number or 'N/A'}) - Desconto de {lot.auto_discount_percentage}%"
            )
    else:
        report_lines.append("Nenhum produto entrou em promoção automática ontem.")

    if newly_unpromoted_lots.exists():
        report_lines.append("\nProdutos que SAÍRAM de promoção por validade:")
        for lot in newly_unpromoted_lots:
            report_lines.append(
                f"  - {lot.product.name} (Lote: {lot.lot_number or 'N/A'})"
            )
    else:
        report_lines.append("\nNenhum produto saiu de promoção automática ontem.")

    report_lines.append("\n\n" + "=" * 50)
    report_lines.append("\n== PROMOÇÕES ATIVAS HOJE ==\n")

    report_lines.append("--- Promoções Manuais ---")
    if active_manual_promotions.exists():
        for promo in active_manual_promotions:
            report_lines.append(
                f"\n* {promo.name} (Válida até {promo.end_date.strftime('%d/%m/%Y')})"
            )
            for rule in promo.rules.all():
                report_lines.append(
                    f"  - {rule.lot.product.name} (Lote: {rule.lot.lot_number or 'N/A'}) - {rule.discount_percentage}% de desconto"
                )
    else:
        report_lines.append("Nenhuma promoção manual ativa hoje.")

    report_lines.append("\n--- Promoções Automáticas por Validade ---")
    if active_auto_promotions.exists():
        for lot in active_auto_promotions:
            report_lines.append(
                f"  - {lot.product.name} (Lote: {lot.lot_number or 'N/A'}) - {lot.auto_discount_percentage}% de desconto"
            )
    else:
        report_lines.append("Nenhuma promoção automática ativa hoje.")

    message = "\n".join(report_lines)

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.ADMIN_EMAIL],
        fail_silently=False,
    )

    return (
        f"Relatório de promoções para {today.strftime('%d/%m/%Y')} enviado com sucesso."
    )
