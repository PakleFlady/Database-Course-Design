"""Views for password policy enforcement."""
from __future__ import annotations

from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

from registrar.models import UserSecurityProfile


class EnforcedPasswordChangeView(PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user.is_authenticated:
            profile, _ = UserSecurityProfile.objects.get_or_create(user=self.request.user)
            profile.mark_password_changed()
        return response
