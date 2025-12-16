"""Views for authentication helpers."""
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from django.urls import reverse_lazy
from django.views.generic import TemplateView

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


class LoginPortalView(TemplateView):
    template_name = "registration/login_portal.html"


class StudentLoginView(LoginView):
    template_name = "registration/student_login.html"
    redirect_authenticated_user = True
    extra_context = {"role_label": "学生", "switch_url_name": "instructor_login"}

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        return redirect_to or reverse_lazy("account_home")


class InstructorLoginView(LoginView):
    template_name = "registration/instructor_login.html"
    redirect_authenticated_user = True
    extra_context = {"role_label": "教师", "switch_url_name": "student_login"}

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        return redirect_to or reverse_lazy("account_home")


class AccountHomeView(LoginRequiredMixin, TemplateView):
    template_name = "registration/account_home.html"


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("login_portal")
