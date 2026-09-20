from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """
    Function-view decorator. Usage:

        @role_required('ADMIN')
        def some_view(request): ...

    Always checks on the server side — never rely on hiding a button alone.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.error(request, "You don't have permission to access that page.")
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Class-based-view mixin. Set `allowed_roles = ['ADMIN', 'MANAGER']` on the view.
    """
    allowed_roles = []

    def test_func(self):
        return self.request.user.role in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "You don't have permission to access that page.")
        raise PermissionDenied


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['ADMIN']


class ManagerOrAdminMixin(RoleRequiredMixin):
    allowed_roles = ['ADMIN', 'MANAGER']


class AnyStaffMixin(RoleRequiredMixin):
    """Admin, Manager, or Employee — i.e. any authenticated staff member."""
    allowed_roles = ['ADMIN', 'MANAGER', 'EMPLOYEE']
