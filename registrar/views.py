"""Views for authentication helpers and self-service portals."""
from __future__ import annotations

from django.contrib import messages
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
from .models import (
    ApprovalLog,
    CoursePrerequisite,
    CourseSection,
    Enrollment,
    MeetingTime,
    StudentRequest,
    UserSecurity,
)


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
    """Always redirect to the login portal to avoid template lookups."""

    def get_next_page(self):
        return reverse_lazy("login_portal")


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
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        request_obj = form.save(commit=False)
        handler = self._get_handler(request_obj.request_type)
        if handler:
            error = handler(request_obj)
            if error:
                form.add_error(None, error)
                return self.render_to_response(self.get_context_data(form=form))
        else:
            request_obj.save()
        return redirect("student_home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form") or self.get_form()
        context["requests"] = (
            StudentRequest.objects.filter(student=self.request.user.student_profile)
            .select_related("section__course", "section__semester")
            .prefetch_related("logs")
        )
        context["enrollments"] = (
            Enrollment.objects.filter(student=self.request.user.student_profile)
            .select_related("section__course", "section__semester")
            .order_by("section__semester__start_date")
        )
        context["available_sections"] = CourseSection.objects.select_related(
            "course", "semester", "instructor__user"
        )
        context["gpa"] = self._calculate_gpa(context["enrollments"])
        return context

    def _get_handler(self, request_type):
        handlers = {
            "enroll": self._handle_enrollment,
            "drop": self._handle_drop,
            "waitlist": self._handle_waitlist,
            "retake": self._handle_pending,
            "cross_college": self._handle_pending,
            "credit_overload": self._handle_pending,
            "waitlist_promotion": self._handle_pending,
        }
        return handlers.get(request_type)

    def _handle_pending(self, request_obj: StudentRequest):
        request_obj.status = "pending"
        request_obj.save()

    def _handle_enrollment(self, request_obj: StudentRequest):
        student = request_obj.student
        section = request_obj.section
        error = self._validate_enrollment(student, section)
        if error:
            return error
        Enrollment.objects.update_or_create(
            student=student,
            section=section,
            defaults={"status": "enrolling"},
        )
        request_obj.status = "approved"
        request_obj.save()
        return None

    def _handle_waitlist(self, request_obj: StudentRequest):
        student = request_obj.student
        section = request_obj.section
        Enrollment.objects.update_or_create(
            student=student,
            section=section,
            defaults={"status": "waitlisted"},
        )
        request_obj.status = "approved"
        request_obj.save()
        return None

    def _handle_drop(self, request_obj: StudentRequest):
        try:
            enrollment = Enrollment.objects.get(student=request_obj.student, section=request_obj.section)
        except Enrollment.DoesNotExist:
            return "尚未选该课程，无法退课。"
        enrollment.status = "dropped"
        enrollment.save(update_fields=["status"])
        request_obj.status = "approved"
        request_obj.save()
        return None

    def _validate_enrollment(self, student, section):
        active_enrollments = Enrollment.objects.filter(
            student=student,
            status__in=["enrolling", "waitlisted"],
        ).select_related("section__course")

        # credit load check
        planned_credits = sum(e.section.course.credits for e in active_enrollments) + section.course.credits
        if planned_credits < 10 or planned_credits > 40:
            return "选课后总学分需在 10-40 之间。"

        # capacity check
        current_count = Enrollment.objects.filter(section=section, status="enrolling").count()
        if current_count >= section.capacity:
            return "该教学班已满员，可尝试候补申请。"

        # time conflict check
        new_slots = MeetingTime.objects.filter(section=section)
        for slot in new_slots:
            conflict = MeetingTime.objects.filter(
                section__in=[e.section for e in active_enrollments],
                day_of_week=slot.day_of_week,
                start_time__lt=slot.end_time,
                end_time__gt=slot.start_time,
            )
            if conflict.exists():
                return "与已选课程存在时间冲突。"

        # prerequisite check
        missing = []
        grade_order = {"A": 4, "B": 3, "C": 2, "D": 1, "P": 2, "F": 0, "NP": 0}
        prereqs = CoursePrerequisite.objects.filter(course=section.course)
        for prereq in prereqs:
            record = Enrollment.objects.filter(
                student=student,
                section__course=prereq.prerequisite,
                final_grade__isnull=False,
            ).first()
            if not record:
                missing.append(prereq.prerequisite.code)
                continue
            if grade_order.get(record.final_grade, 0) < grade_order.get(prereq.min_grade, 0):
                missing.append(prereq.prerequisite.code)
        if missing:
            return "未满足先修要求：" + ", ".join(missing)
        return None

    def _calculate_gpa(self, enrollments):
        grade_points = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0, "P": 2.0, "NP": 0.0}
        total_points = 0
        total_credits = 0
        for enroll in enrollments:
            if enroll.final_grade:
                pts = grade_points.get(enroll.final_grade)
                if pts is None:
                    continue
                total_points += float(enroll.section.course.credits) * pts
                total_credits += float(enroll.section.course.credits)
        if total_credits == 0:
            return None
        return round(total_points / total_credits, 2)


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
        context["enrollments"] = (
            Enrollment.objects.filter(section__in=context["sections"])
            .select_related("student__user", "section__course", "section__semester")
            .order_by("section__course__code")
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
        context["sections"] = CourseSection.objects.select_related(
            "course", "semester", "instructor__user"
        ).order_by("semester__start_date")
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


class InstructorGradeUpdateView(LoginRequiredMixin, View):
    def post(self, request, section_id):
        if not hasattr(request.user, "instructor_profile"):
            return HttpResponseForbidden("仅教师可录入成绩")

        try:
            section = CourseSection.objects.get(pk=section_id, instructor=request.user.instructor_profile)
        except CourseSection.DoesNotExist:
            return HttpResponseForbidden("未找到教学班或无权限")

        if section.grades_locked:
            messages.error(request, "该教学班成绩已锁定，无法修改。")
            return redirect("instructor_home")

        enrollment_id = request.POST.get("enrollment_id")
        grade = request.POST.get("final_grade")
        status = request.POST.get("status", "enrolling")

        if grade and grade not in dict(Enrollment.GRADE_CHOICES):
            messages.error(request, "成绩格式不正确。")
            return redirect("instructor_home")

        try:
            enrollment = Enrollment.objects.get(pk=enrollment_id, section=section)
        except Enrollment.DoesNotExist:
            messages.error(request, "未找到选课记录。")
            return redirect("instructor_home")

        enrollment.final_grade = grade
        enrollment.status = status
        enrollment.grade_points = self._grade_to_points(grade)
        enrollment.save(update_fields=["final_grade", "status", "grade_points"])
        messages.success(request, "已更新成绩记录。")
        return redirect("instructor_home")

    def _grade_to_points(self, grade: str | None):
        mapping = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0, "P": 2.0, "NP": 0.0}
        return mapping.get(grade)


class AdminSectionLockToggleView(LoginRequiredMixin, View):
    def post(self, request, section_id):
        if not request.user.is_staff:
            return HttpResponseForbidden("仅管理员可锁定或解锁成绩填报")

        try:
            section = CourseSection.objects.get(pk=section_id)
        except CourseSection.DoesNotExist:
            messages.error(request, "未找到教学班。")
            return redirect("admin_home")

        section.grades_locked = not section.grades_locked
        section.save(update_fields=["grades_locked"])
        messages.success(request, "已{}成绩填报。".format("锁定" if section.grades_locked else "解锁"))
        return redirect("admin_home")
