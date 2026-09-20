from rest_framework.permissions import BasePermission

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')


class IsManagerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and request.user.role in ('ADMIN', 'MANAGER')
        )


class IsAnyStaff(BasePermission):
    """Any authenticated role — Admin, Manager, or Employee."""
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and request.user.role in ('ADMIN', 'MANAGER', 'EMPLOYEE')
        )


class ReadOnlyOrManagerAdmin(BasePermission):
    """Any staff can read; only Manager/Admin can write (matches Employee's read-only access)."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return request.user.role in ('ADMIN', 'MANAGER', 'EMPLOYEE')
        return request.user.role in ('ADMIN', 'MANAGER')
