"""Views for authentication helpers."""
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeDoneView, PasswordChangeView
from django.urls import reverse_lazy

from .models import UserSecurity


class ForcePasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "registration/force_password_change_form.html"
    success_url = reverse_lazy("password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        security, _ = UserSecurity.objects.get_or_create(user=self.request.user)
        security.must_change_password = False
        security.save(update_fields=["must_change_password"])
        return response

    def get_success_url(self):
        redirect_target = self.request.POST.get("next") or self.request.GET.get("next")
        base_url = super().get_success_url()
        if redirect_target:
            return f"{base_url}?next={redirect_target}"
        return base_url


class ForcePasswordChangeDoneView(LoginRequiredMixin, PasswordChangeDoneView):
    template_name = "registration/force_password_change_done.html"
