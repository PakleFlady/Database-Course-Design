"""Middleware to enforce password change on first login when using default credentials."""
from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import resolve, reverse

from registrar.models import UserSecurityProfile


class EnforcePasswordChangeMiddleware:
    """Redirect authenticated users to change their password when required."""

    allowed_url_names = {
        "password_change",
        "password_change_done",
        "logout",
        "admin:logout",
        "admin:password_change",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile, _ = UserSecurityProfile.objects.get_or_create(user=request.user)
            if profile.force_password_change:
                if not self._is_allowed_path(request):
                    messages.info(
                        request,
                        "出于安全考虑，请先修改默认密码后再继续操作。",
                    )
                    return redirect(reverse("password_change"))

        return self.get_response(request)

    def _is_allowed_path(self, request) -> bool:
        """Allow access to password change, logout and static assets to avoid loops."""
        resolver_match = None
        try:
            resolver_match = resolve(request.path_info)
        except Exception:  # pragma: no cover - resolve may fail on non-matched paths
            resolver_match = None

        if resolver_match and resolver_match.view_name in self.allowed_url_names:
            return True

        static_url = getattr(settings, "STATIC_URL", "/static/")
        return request.path_info.startswith(static_url)
