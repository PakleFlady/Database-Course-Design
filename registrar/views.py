"""Views for authentication helpers and self-service portals."""
from __future__ import annotations

from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from .forms import ApprovalDecisionForm, SelfServiceRequestForm
from .models import CourseSection, StudentRequest, UserSecurity


class ForcePasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "registration/force_password_change_form.html"
    success_url = reverse_lazy("password_change_done")
    form_class = SetPasswordForm

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

    def get(self, request, *args, **kwargs):
        user = request.user
        if hasattr(user, "student_profile"):
            return redirect("student_home")
        if hasattr(user, "instructor_profile"):
            return redirect("instructor_home")
        if user.is_staff:
            return redirect("admin_home")
        return super().get(request, *args, **kwargs)


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("login_portal")


class StudentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "registration/dashboard_student.html"

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "student_profile"):
            return HttpResponseForbidden("仅学生可访问此页面")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self):
        return SelfServiceRequestForm(student=self.request.user.student_profile)

    def post(self, request, *args, **kwargs):
        form = SelfServiceRequestForm(request.POST, student=request.user.student_profile)
        if form.is_valid():
            form.save()
            return redirect("student_home")
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form") or self.get_form()
        context["requests"] = (
            StudentRequest.objects.filter(student=self.request.user.student_profile)
            .select_related("section__course", "section__semester")
            .prefetch_related("logs")
        )
        return context


class InstructorDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "registration/dashboard_instructor.html"

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "instructor_profile"):
            return HttpResponseForbidden("仅教师可访问此页面")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instructor = self.request.user.instructor_profile
        context["sections"] = CourseSection.objects.filter(instructor=instructor).select_related(
            "course", "semester"
        )
        context["pending_requests"] = (
            StudentRequest.objects.filter(
                section__in=context["sections"],
                status="pending",
                request_type__in=["retake", "cross_college", "credit_overload", "waitlist_promotion"],
            )
            .select_related("student__user", "section__course", "section__semester")
            .prefetch_related("logs")
        )
        return context


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "registration/dashboard_admin.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden("仅管理员可访问此页面")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_requests"] = StudentRequest.objects.filter(status="pending").select_related(
            "student__user", "section__course", "section__semester"
        )
        return context


class ApprovalQueueView(LoginRequiredMixin, TemplateView):
    template_name = "registration/approval_queue.html"

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_staff or hasattr(request.user, "instructor_profile")):
            return HttpResponseForbidden("仅教师或管理员可审核")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = StudentRequest.objects.filter(
            status="pending",
            request_type__in=["retake", "cross_college", "credit_overload", "waitlist_promotion"],
        ).select_related("student__user", "section__course", "section__semester")

        if hasattr(self.request.user, "instructor_profile") and not self.request.user.is_staff:
            sections = CourseSection.objects.filter(instructor=self.request.user.instructor_profile)
            queryset = queryset.filter(section__in=sections)

        context["pending_requests"] = queryset
        context["decision_form"] = ApprovalDecisionForm()
        return context


class ApprovalDecisionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            req_obj = StudentRequest.objects.select_related("section__instructor").get(pk=pk)
        except StudentRequest.DoesNotExist:
            return HttpResponseForbidden("记录不存在")

        if not (request.user.is_staff or (
            hasattr(request.user, "instructor_profile") and req_obj.section and req_obj.section.instructor == request.user.instructor_profile
        )):
            return HttpResponseForbidden("无权限审批该申请")

        form = ApprovalDecisionForm(request.POST)
        if not form.is_valid():
            return redirect("approval_queue")

        decision = form.cleaned_data["decision"]
        note = form.cleaned_data.get("note", "")

        req_obj.status = decision
        req_obj.reviewed_by = request.user
        req_obj.reviewed_at = timezone.now()
        req_obj.save(update_fields=["status", "reviewed_by", "reviewed_at"])

        from .models import ApprovalLog

        ApprovalLog.objects.create(request=req_obj, action=decision, actor=request.user, note=note)
        return redirect("approval_queue")
