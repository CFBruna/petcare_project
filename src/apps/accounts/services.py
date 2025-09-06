from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from django.contrib.auth.models import User
from django.db import transaction

if TYPE_CHECKING:
    from src.apps.accounts.models import Customer

logger = structlog.get_logger(__name__)


class CustomerService:
    @staticmethod
    @transaction.atomic
    def create_customer(
        *, username: str, first_name: str, phone: str, cpf: str
    ) -> "Customer":  # noqa: UP037
        """
        Creates a new User and an associated Customer profile.
        """
        from src.apps.accounts.models import Customer

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
        )
        customer = Customer.objects.create(
            user=user,
            phone=phone,
            cpf=cpf,
        )
        logger.info(
            "customer_created",
            customer_id=customer.id,
            user_id=user.id,
            username=user.username,
        )
        return customer
