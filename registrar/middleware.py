"""Custom middleware for enforcing security rules."""
from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse

from .models import UserSecurity


class ForcePasswordChangeMiddleware:
    """Redirect authenticated users to change their password when required."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            security, _ = UserSecurity.objects.get_or_create(user=user)
            try:
                change_url = reverse("force_password_change")
                done_url = reverse("password_change_done")
            except NoReverseMatch:
                change_url = done_url = ""

            try:
                logout_url = reverse("logout")
            except NoReverseMatch:
                logout_url = getattr(settings, "LOGOUT_URL", "/admin/logout/")

            allowed_paths = {
                change_url,
                done_url,
                logout_url,
            }

            is_static = bool(getattr(settings, "STATIC_URL", "")) and request.path.startswith(settings.STATIC_URL)
            if (
                security.must_change_password
                and not user.is_staff
                and not is_static
                and request.path not in allowed_paths
            ):
                messages.warning(request, "首次登录需要修改默认密码，请先完成密码更新。")
                return redirect(f"{change_url}?next={request.path}")

        response = self.get_response(request)
        return response
