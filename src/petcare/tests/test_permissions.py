import pytest
from django.test import RequestFactory

from src.apps.accounts.tests.factories import CustomerFactory, UserFactory
from src.apps.pets.tests.factories import PetFactory
from src.apps.schedule.tests.factories import AppointmentFactory
from src.petcare.permissions import IsOwnerOrStaff


class MockView:
    pass


@pytest.mark.django_db
class TestIsOwnerOrStaffPermission:
    def setup_method(self):
        self.permission = IsOwnerOrStaff()
        self.view = MockView()
        self.factory = RequestFactory()
        self.staff_user = UserFactory(is_staff=True)
        self.regular_user = UserFactory()
        self.customer = CustomerFactory(user=self.regular_user)

    def test_staff_user_has_object_permission(self):
        request = self.factory.get("/")
        request.user = self.staff_user
        obj = PetFactory()
        assert self.permission.has_object_permission(request, self.view, obj) is True

    def test_owner_has_object_permission_direct(self):
        request = self.factory.get("/")
        request.user = self.regular_user
        obj = PetFactory(owner=self.customer)
        assert self.permission.has_object_permission(request, self.view, obj) is True

    def test_owner_has_object_permission_indirect(self):
        request = self.factory.get("/")
        request.user = self.regular_user
        pet = PetFactory(owner=self.customer)
        obj = AppointmentFactory(pet=pet)
        assert self.permission.has_object_permission(request, self.view, obj) is True

    def test_other_user_does_not_have_permission(self):
        request = self.factory.get("/")
        request.user = UserFactory()
        obj = PetFactory(owner=self.customer)
        assert self.permission.has_object_permission(request, self.view, obj) is False

    def test_object_with_no_owner_attribute(self):
        request = self.factory.get("/")
        request.user = self.regular_user
        obj = object()
        assert self.permission.has_object_permission(request, self.view, obj) is False
