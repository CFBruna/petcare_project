import pytest
from django.utils import timezone

from src.apps.schedule.models import Appointment
from src.apps.schedule.tasks import generate_daily_appointments_report
from src.apps.schedule.tests.factories import AppointmentFactory


@pytest.mark.django_db
def test_generate_daily_report_with_completed_appointments(mocker):
    # Arrange:
    mocked_now = timezone.make_aware(timezone.datetime(2025, 8, 26, 10, 0))
    mocker.patch("django.utils.timezone.now", return_value=mocked_now)
    mocker.patch("django.utils.timezone.localdate", return_value=mocked_now.date())

    send_mail_mock = mocker.patch("src.apps.schedule.tasks.send_mail")

    yesterday_date = mocked_now.date() - timezone.timedelta(days=1)

    completed_appointment = AppointmentFactory(
        status=Appointment.Status.COMPLETED,
        completed_at=mocked_now - timezone.timedelta(days=1),
    )

    AppointmentFactory(status=Appointment.Status.PENDING)
    AppointmentFactory(status=Appointment.Status.COMPLETED, completed_at=mocked_now)

    # Act:
    result = generate_daily_appointments_report()

    send_mail_mock.assert_called_once()

    call_args = send_mail_mock.call_args[0]
    subject = call_args[0]
    message = call_args[1]

    assert "Relatório Diário de Agendamentos Concluídos" in subject
    assert "(1 agendamentos)" in subject
    assert completed_appointment.pet.name in message
    assert (
        result
        == f"Relatório de agendamentos concluídos para {yesterday_date.strftime('%d/%m/%Y')} enviado com sucesso."
    )


@pytest.mark.django_db
def test_generate_daily_report_with_no_completed_appointments(mocker):
    # Arrange
    mocked_now = timezone.make_aware(timezone.datetime(2025, 8, 26, 10, 0))
    mocker.patch("django.utils.timezone.now", return_value=mocked_now)
    mocker.patch("django.utils.timezone.localdate", return_value=mocked_now.date())

    send_mail_mock = mocker.patch("src.apps.schedule.tasks.send_mail")

    yesterday_date = mocked_now.date() - timezone.timedelta(days=1)

    AppointmentFactory(status=Appointment.Status.PENDING)
    AppointmentFactory(status=Appointment.Status.COMPLETED, completed_at=mocked_now)

    # Act
    result = generate_daily_appointments_report()

    # Assert
    send_mail_mock.assert_called_once()

    call_args = send_mail_mock.call_args[0]
    message = call_args[1]

    assert "Nenhum agendamento foi concluído nesta data." in message
    assert (
        result
        == f"Relatório de agendamentos concluídos para {yesterday_date.strftime('%d/%m/%Y')} enviado com sucesso."
    )
