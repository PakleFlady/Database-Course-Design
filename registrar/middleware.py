"""Custom middleware used by the registrar app."""

from __future__ import annotations

from django.conf import settings
from django.shortcuts import redirect
from django.urls import Resolver404, resolve


class ForcePasswordChangeMiddleware:
    """Redirect authenticated users to change password when required."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.process_request(request)
        if response:
            return response
        return self.get_response(request)

    def process_request(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        security_profile = getattr(user, "security_profile", None)
        if not security_profile or not security_profile.must_change_password:
            return None

        try:
            resolved = resolve(request.path_info)
        except Resolver404:
            return None
        allowed_names = {
            "admin:password_change",
            "password_change_done",
            "force_password_change",
            "admin:logout",
            "logout",
        }

        if resolved.view_name in allowed_names:
            return None

        if request.path.startswith(settings.STATIC_URL):
            return None

        return redirect("force_password_change")

