from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsStaffOrReadOnly(BasePermission):
    """
    Custom permission to allow read-only access for any authenticated user,
    while restricting write access (POST, PUT, PATCH, DELETE) to staff
    members only.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return request.user.is_staff


class IsOwnerOrStaff(BasePermission):
    """
    Custom permission to only allow owners of an object or staff to access it.
    Assumes the model instance has an `owner` attribute, or a `pet.owner` attribute.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if hasattr(obj, "pet") and hasattr(obj.pet, "owner"):
            return obj.pet.owner.user == request.user

        if hasattr(obj, "owner"):
            return obj.owner.user == request.user

        return False
