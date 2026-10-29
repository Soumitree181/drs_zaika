from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_panel_required(view_func):
    """
    Decorator that strictly permits only Partners, Staff, and Admins.
    Students are strictly forbidden from performing any operations in the admin panel.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.can_access_admin_panel:
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def partner_or_admin_required(view_func):
    """
    Decorator restricting user management operations exclusively to Partners and Admins.
    Staff members can manage Students and Student Types, but cannot alter User accounts or roles.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.can_access_admin_panel:
            return redirect('access_denied')
        if not (request.user.can_manage_users or request.user.is_partner or request.user.is_superuser):
            messages.error(
                request,
                "Permission Denied: This operation is restricted to Partners and Administrators only."
            )
            return redirect('admin_dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
