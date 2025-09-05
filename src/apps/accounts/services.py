from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.db import transaction

if TYPE_CHECKING:
    from src.apps.accounts.models import Customer

logger = logging.getLogger(__name__)


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
            "New customer '%s' (ID: %d) created via CustomerService.",
            customer.user.username,
            customer.id,
        )
        return customer
