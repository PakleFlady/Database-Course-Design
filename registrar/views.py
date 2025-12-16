"""Views for registrar app."""

from __future__ import annotations

from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy


class ForcePasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        security_profile = getattr(self.request.user, "security_profile", None)
        if security_profile and security_profile.must_change_password:
            security_profile.must_change_password = False
            security_profile.save(update_fields=["must_change_password"])
        return response


class ForcePasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    template_name = "registration/password_change_done.html"
