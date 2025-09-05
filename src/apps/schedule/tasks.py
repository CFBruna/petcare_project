from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Sum
from django.utils import timezone

from .models import Appointment


@shared_task
def generate_daily_appointments_report() -> str:
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    completed_appointments = (
        Appointment.objects.filter(
            status=Appointment.Status.COMPLETED, completed_at__date=yesterday
        )
        .select_related("pet__owner__user", "service")
        .order_by("completed_at")
    )

    total_revenue = (
        completed_appointments.aggregate(total=Sum("service__price"))["total"] or 0
    )

    if not completed_appointments.exists():
        subject = f"Relatório Diário de Agendamentos Concluídos - {yesterday.strftime('%d/%m/%Y')}"
        message = "Nenhum agendamento foi concluído nesta data."
    else:
        subject = f"Relatório Diário de Agendamentos Concluídos - {yesterday.strftime('%d/%m/%Y')} ({completed_appointments.count()} agendamentos)"
        report_lines = [
            f"Relatório de agendamentos concluídos em {yesterday.strftime('%d/%m/%Y')}:",
            "-" * 40,
        ]

        for app in completed_appointments:
            pet_name = app.pet.name
            tutor_name = app.pet.owner.full_name or app.pet.owner.user.username
            service_name = app.service.name
            service_price = app.service.price
            completed_time = (
                timezone.localtime(app.completed_at).strftime("%H:%M")
                if app.completed_at
                else "N/A"
            )

            report_lines.append(
                f"- {completed_time}h: {service_name} para {pet_name} (Tutor: {tutor_name}) - R$ {service_price:.2f}"
            )

        report_lines.append("-" * 40)
        report_lines.append(f"Faturamento Total do Dia: R$ {total_revenue:.2f}")

        message = "\n".join(report_lines)

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.ADMIN_EMAIL],
        fail_silently=False,
    )

    return f"Relatório de agendamentos concluídos para {yesterday.strftime('%d/%m/%Y')} enviado com sucesso."
