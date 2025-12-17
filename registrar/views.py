"""Views for authentication helpers and self-service portals."""
from __future__ import annotations

import csv
import datetime
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import login
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from django.db.models import Count, Q, F, Sum, Avg, Max, Min
from django.db.models.functions import Greatest
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, FormView

from .forms import (
    AdminBulkEnrollmentForm,
    AdminClassScheduleForm,
    ApprovalDecisionForm,
    AccountRegistrationForm,
    InstructorAuthenticationForm,
    InstructorContactForm,
    SelfServiceRequestForm,
    StudentAuthenticationForm,
    StudentContactForm,
)
from .models import (
    ApprovalLog,
    Course,
    CoursePrerequisite,
    CourseSection,
    Department,
    Enrollment,
    MeetingTime,
    ProgramPlan,
    ProgramRequirement,
    StudentProfile,
    StudentRequest,
    UserSecurity,
)


def grade_to_points(grade):
    try:
        numeric = float(grade)
    except (TypeError, ValueError):
        return None
    if numeric >= 90:
        return 4.0
    if numeric >= 80:
        return 3.0
    if numeric >= 70:
        return 2.0
    if numeric >= 60:
        return 1.0
    return 0.0


def is_passing_grade(grade):
    try:
        return float(grade) >= 60
    except (TypeError, ValueError):
        return False


def calculate_gpa_from_enrollments(enrollments):
    total_points = 0
    total_credits = 0
    for enroll in enrollments:
        pts = grade_to_points(enroll.final_grade)
        if pts is None:
            continue
        total_points += float(enroll.section.course.credits) * pts
        total_credits += float(enroll.section.course.credits)
    if total_credits == 0:
        return None
    return round(total_points / total_credits, 2)


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
    authentication_form = StudentAuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        # 始终在进入登录页时清除已有会话，避免自动跳回原账户
        if request.user.is_authenticated:
            logout(request)
            return redirect(request.path)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        return redirect_to or reverse_lazy("account_home")


class InstructorLoginView(LoginView):
    template_name = "registration/instructor_login.html"
    redirect_authenticated_user = True
    extra_context = {"role_label": "教师", "switch_url_name": "student_login"}
    authentication_form = InstructorAuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
            return redirect(request.path)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        return redirect_to or reverse_lazy("account_home")


class AccountRegistrationView(FormView):
    template_name = "registration/register.html"
    form_class = AccountRegistrationForm
    success_url = reverse_lazy("login_portal")

    def form_valid(self, form):
        user = form.save()
        role = form.cleaned_data.get("role")
        if role == "instructor":
            messages.success(self.request, "注册成功，账号待管理员审批后方可登录。")
        else:
            login(self.request, user)
            messages.success(self.request, "注册成功，已自动登录，请完善个人信息。")
        return super().form_valid(form)


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
    """Show a friendly logout confirmation page instead of silent redirect."""

    # 始终回到登录入口，方便用户在退出后立即选择学生或教师身份重新登录
    next_page = reverse_lazy("login_portal")
    template_name = "registration/logout_success.html"


class EnrollmentValidationMixin:
    def _validate_enrollment(self, student, section):
        active_enrollments = Enrollment.objects.filter(
            student=student,
            status="enrolling",
        ).select_related("section__course")

        passed_before = Enrollment.objects.filter(
            student=student,
            section__course=section.course,
            status="passed",
        ).exists()
        if passed_before:
            approved_retake = StudentRequest.objects.filter(
                student=student,
                request_type="retake",
                section__course=section.course,
                status="approved",
            ).exists()
            if not approved_retake:
                return "已通过该课程，如需重修请先提交并通过教务管理员审批。"

        planned_credits = sum(e.section.course.credits for e in active_enrollments) + section.course.credits
        if planned_credits > 40:
            return "选课后总学分不得超过 40 学分。"

        current_count = Enrollment.objects.filter(section=section, status="enrolling").count()
        if current_count >= section.capacity:
            return "该教学班已满员，暂无法继续选课。"

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

        missing = []
        grade_threshold = {"A": 90, "B": 80, "C": 70, "D": 60, "P": 60, "NP": 0, "F": 0}
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
            threshold = grade_threshold.get(prereq.min_grade, 0)
            try:
                actual = float(record.final_grade)
            except (TypeError, ValueError):
                missing.append(prereq.prerequisite.code)
                continue
            if actual < threshold:
                missing.append(prereq.prerequisite.code)
        if missing:
            return "未满足先修要求：" + ", ".join(missing)
        return None

    def _calculate_gpa(self, enrollments):
        return calculate_gpa_from_enrollments(enrollments)


class StudentPortalMixin(LoginRequiredMixin, EnrollmentValidationMixin):
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "student_profile"):
            return HttpResponseForbidden("仅学生可访问此页面")
        return super().dispatch(request, *args, **kwargs)

    def _build_student_context(self):
        profile = self.request.user.student_profile
        request_qs = StudentRequest.objects.filter(student=profile).select_related(
            "section__course", "section__semester"
        )
        enrollments = list(
            Enrollment.objects.filter(student=profile)
            .select_related("section__course", "section__semester")
            .order_by("section__semester__start_date")
        )
        active_sections = [
            enrollment.section
            for enrollment in enrollments
            if enrollment.status in ["enrolling", "passed", "failed"]
        ]

        return {
            "profile": profile,
            "requests": request_qs.prefetch_related("logs"),
            "request_summary": {
                "pending": request_qs.filter(status="pending").count(),
                "approved": request_qs.filter(status="approved").count(),
                "rejected": request_qs.filter(status="rejected").count(),
            },
            "enrollments": enrollments,
            "available_section_count": CourseSection.objects.filter(course__department=profile.department).count(),
            "gpa": self._calculate_gpa(enrollments),
            "credit_load": sum(
                enrollment.section.course.credits
                for enrollment in enrollments
                if enrollment.status == "enrolling"
            ),
            "schedule": MeetingTime.objects.filter(section__in=active_sections).select_related(
                "section__course", "section__semester"
            ),
            "failed_enrollments": [
                enrollment
                for enrollment in enrollments
                if enrollment.status == "failed" or enrollment.final_grade in ["F", "NP"]
            ],
        }

    def _get_handler(self, request_type):
        handlers = {
            "retake": self._handle_pending,
            "cross_college": self._handle_pending,
            "credit_overload": self._handle_pending,
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


class StudentDashboardView(StudentPortalMixin, TemplateView):
    template_name = "registration/dashboard_student.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._build_student_context())
        return context


class StudentProfileView(StudentPortalMixin, TemplateView):
    template_name = "registration/student_profile.html"

    def post(self, request, *args, **kwargs):
        form = StudentContactForm(request.POST, instance=request.user.student_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "联系方式已更新。")
            return redirect("student_profile")
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._build_student_context())
        context["form"] = kwargs.get("form") or StudentContactForm(instance=self.request.user.student_profile)
        return context


class StudentSelfServiceView(StudentPortalMixin, TemplateView):
    template_name = "registration/student_selfservice.html"

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
                messages.error(request, error)
                return self.render_to_response(self.get_context_data(form=form))
        else:
            request_obj.save()
        messages.success(request, "请求已提交，请留意状态变更。")
        return redirect("student_self_service")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._build_student_context())
        context["form"] = kwargs.get("form") or self.get_form()
        return context


class StudentScheduleView(StudentPortalMixin, TemplateView):
    template_name = "registration/student_schedule.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._build_student_context())
        return context


class StudentGradesView(StudentPortalMixin, TemplateView):
    template_name = "registration/student_grades.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._build_student_context())
        return context


class StudentRequestLogView(StudentPortalMixin, TemplateView):
    template_name = "registration/student_requests.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._build_student_context())
        return context


class StudentEnrollmentView(StudentPortalMixin, TemplateView):
    template_name = "registration/course_selection.html"

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "student_profile"):
            return HttpResponseForbidden("仅学生可访问此页面")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.student_profile
        enrollments = Enrollment.objects.filter(student=profile, status="enrolling").select_related(
            "section__course", "section__semester", "section__instructor__user"
        )
        available_sections = (
            CourseSection.objects.filter(course__department=profile.department)
            .select_related("course", "semester", "instructor__user")
            .prefetch_related("meeting_times")
            .annotate(
                enrolled_count=Count(
                    "enrollments", filter=Q(enrollments__status="enrolling"), distinct=True
                )
            )
            .annotate(remaining_capacity=Greatest(F("capacity") - F("enrolled_count"), 0))
            .order_by("course__code", "section_number")
        )

        context["profile"] = profile
        context["enrollments"] = enrollments
        context["available_sections"] = available_sections
        context["enrollment_ids"] = [e.section_id for e in enrollments]
        return context

    def post(self, request, *args, **kwargs):
        if not hasattr(request.user, "student_profile"):
            return HttpResponseForbidden("仅学生可访问此页面")

        action = request.POST.get("action")
        section_id = request.POST.get("section_id")
        profile = request.user.student_profile

        try:
            section = CourseSection.objects.select_related("course").get(pk=section_id)
        except CourseSection.DoesNotExist:
            messages.error(request, "未找到教学班。")
            return redirect("student_enrollment")

        if section.course.department != profile.department:
            messages.error(request, "只能选择本学院开设的课程。")
            return redirect("student_enrollment")

        if action == "enroll":
            error = self._validate_enrollment(profile, section)
            if error:
                messages.error(request, error)
                return redirect("student_enrollment")
            Enrollment.objects.update_or_create(
                student=profile,
                section=section,
                defaults={"status": "enrolling"},
            )
            messages.success(request, "选课成功，已加入课堂。")
        elif action == "drop":
            try:
                enrollment = Enrollment.objects.get(student=profile, section=section, status="enrolling")
            except Enrollment.DoesNotExist:
                messages.error(request, "尚未选该课程或已退课。")
                return redirect("student_enrollment")
            remaining_credits = (
                Enrollment.objects.filter(student=profile, status="enrolling")
                .exclude(pk=enrollment.pk)
                .select_related("section__course")
                .aggregate(total=Sum("section__course__credits"))
                .get("total")
                or 0
            )
            if remaining_credits < 10:
                messages.error(request, "退课后总学分将低于 10 学分，无法退课。")
                return redirect("student_enrollment")
            enrollment.status = "dropped"
            enrollment.save(update_fields=["status"])
            messages.success(request, "已退选该课程。")
        else:
            messages.error(request, "未知操作。")
        return redirect("student_enrollment")

class StudentScheduleExportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if not hasattr(request.user, "student_profile"):
            return HttpResponseForbidden("仅学生可导出课表")

        enrollments = Enrollment.objects.filter(
            student=request.user.student_profile,
            status__in=["enrolling", "passed", "failed"],
        ).values_list("section", flat=True)

        credit_load = (
            Enrollment.objects.filter(
                student=request.user.student_profile,
                status__in=["enrolling", "passed", "failed"],
            )
            .select_related("section__course")
            .aggregate(total=Sum("section__course__credits"))
            .get("total")
            or 0
        )
        if credit_load < 10 or credit_load > 40:
            return HttpResponse(
                f"计划学分需在 10-40 学分之间，当前为 {float(credit_load):.1f}。",
                status=400,
            )

        meeting_times = MeetingTime.objects.filter(section_id__in=enrollments).select_related(
            "section__course", "section__semester", "section__instructor__user"
        )

        # 生成按时间段（行）与星期（列）的表格课表
        days = [choice[0] for choice in MeetingTime.DAY_OF_WEEK_CHOICES]
        day_labels = {choice[0]: choice[1] for choice in MeetingTime.DAY_OF_WEEK_CHOICES}
        slot_matrix = defaultdict(lambda: defaultdict(list))

        for slot in meeting_times:
            key = (slot.start_time, slot.end_time)
            course_label = (
                f"{slot.section.course.name}\n"
                f"{slot.section.course.code}-S{slot.section.section_number}\n"
                f"{slot.section.instructor.user.get_full_name() or slot.section.instructor.user.username}"
            )
            location = slot.location or "待定"
            slot_matrix[key][slot.day_of_week].append(f"{course_label}\n@{location}")

        ordered_slots = sorted(slot_matrix.keys(), key=lambda t: t[0])

        response = HttpResponse(content_type="text/csv")
        filename = f"schedule_{request.user.username}_grid.csv"
        response["Content-Disposition"] = f"attachment; filename={filename}"

        writer = csv.writer(response)
        writer.writerow(["时间段"] + [day_labels[d] for d in days])
        for slot_range in ordered_slots:
            row = [f"{slot_range[0]}-{slot_range[1]}"]
            for day in days:
                cell = "\n---\n".join(slot_matrix[slot_range].get(day, []))
                row.append(cell)
            writer.writerow(row)

        return response


class StudentTranscriptExportView(StudentPortalMixin, View):
    def get(self, request, *args, **kwargs):
        enrollments = (
            Enrollment.objects.filter(student=request.user.student_profile)
            .select_related("section__course", "section__semester")
            .order_by("section__semester__start_date", "section__course__code")
        )

        response = HttpResponse(content_type="text/csv")
        filename = f"transcript_{request.user.username}.csv"
        response["Content-Disposition"] = f"attachment; filename={filename}"

        writer = csv.writer(response)
        writer.writerow(["学期", "课程代码", "课程名称", "学分", "状态", "成绩", "绩点"])
        for enrollment in enrollments:
            writer.writerow(
                [
                    enrollment.section.semester.code,
                    enrollment.section.course.code,
                    enrollment.section.course.name,
                    enrollment.section.course.credits,
                    enrollment.get_status_display(),
                    enrollment.final_grade if enrollment.final_grade is not None else "-",
                    enrollment.grade_points or "-",
                ]
            )
        return response


class CurriculumPlanView(LoginRequiredMixin, TemplateView):
    template_name = "registration/curriculum_plan.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dept_code = self.request.GET.get("department")
        major_keyword = self.request.GET.get("major")

        plans = (
            ProgramPlan.objects.filter(is_active=True)
            .select_related("department")
            .prefetch_related("requirements__courses")
        )
        if hasattr(self.request.user, "student_profile"):
            dept = self.request.user.student_profile.department
            major = self.request.user.student_profile.major
            if dept:
                plans = plans.filter(department=dept)
            if major:
                plans = plans.filter(major__icontains=major)
        elif hasattr(self.request.user, "instructor_profile") and not self.request.user.is_staff:
            dept = self.request.user.instructor_profile.department
            plans = plans.filter(department=dept)
        if dept_code:
            plans = plans.filter(department__code__iexact=dept_code)
        if major_keyword:
            plans = plans.filter(major__icontains=major_keyword)

        plan_cards = []
        today = datetime.date.today()
        for plan in plans:
            requirements = list(plan.requirements.all())
            category_summary: dict[str, float] = defaultdict(float)
            for req in requirements:
                category_summary[req.get_category_display()] += float(req.required_credits)
            plan_cards.append(
                {
                    "plan": plan,
                    "requirements": requirements,
                    "category_summary": list(category_summary.items()),
                    "is_open": bool(plan.enrollment_start and plan.enrollment_end and plan.enrollment_start <= today <= plan.enrollment_end),
                }
            )

        context.update(
            {
                "plans": plan_cards,
                "departments": Department.objects.all(),
                "filters": {"department": dept_code or "", "major": major_keyword or ""},
                "show_admin_link": self.request.user.is_staff,
            }
        )
        return context


class InstructorScheduleExportView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if not hasattr(request.user, "instructor_profile"):
            return HttpResponseForbidden("仅教师可导出课表")

        sections = CourseSection.objects.filter(instructor=request.user.instructor_profile).values_list(
            "id", flat=True
        )

        meeting_times = MeetingTime.objects.filter(section_id__in=sections).select_related(
            "section__course", "section__semester", "section__instructor__user"
        )

        days = [choice[0] for choice in MeetingTime.DAY_OF_WEEK_CHOICES]
        day_labels = {choice[0]: choice[1] for choice in MeetingTime.DAY_OF_WEEK_CHOICES}
        slot_matrix = defaultdict(lambda: defaultdict(list))

        for slot in meeting_times:
            key = (slot.start_time, slot.end_time)
            course_label = (
                f"{slot.section.course.name}\n"
                f"{slot.section.course.code}-S{slot.section.section_number}\n"
                f"{slot.section.semester.code}"
            )
            location = slot.location or "待定"
            slot_matrix[key][slot.day_of_week].append(f"{course_label}\n@{location}")

        ordered_slots = sorted(slot_matrix.keys(), key=lambda t: t[0])

        response = HttpResponse(content_type="text/csv")
        filename = f"schedule_{request.user.username}_instructor.csv"
        response["Content-Disposition"] = f"attachment; filename={filename}"

        writer = csv.writer(response)
        writer.writerow(["时间段"] + [day_labels[d] for d in days])
        for slot_range in ordered_slots:
            row = [f"{slot_range[0]}-{slot_range[1]}"]
            for day in days:
                cell = "\n---\n".join(slot_matrix[slot_range].get(day, []))
                row.append(cell)
            writer.writerow(row)

        return response


class InstructorDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "registration/dashboard_instructor.html"

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "instructor_profile"):
            return HttpResponseForbidden("仅教师可访问此页面")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instructor = self.request.user.instructor_profile
        sections = list(
            CourseSection.objects.filter(instructor=instructor)
            .select_related("course", "semester")
            .prefetch_related("meeting_times")
        )
        pending_requests = StudentRequest.objects.filter(
            section__in=sections,
            status="pending",
            request_type__in=["retake", "cross_college", "credit_overload"],
        ).select_related("student__user", "section__course", "section__semester")

        enrollments = list(
            Enrollment.objects.filter(section__in=sections)
            .select_related("student__user", "section__course", "section__semester")
            .order_by("section__course__code")
        )

        per_section_counts: dict[int, dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0, "in_progress": 0})
        for enrollment in enrollments:
            bucket = per_section_counts[enrollment.section_id]
            if enrollment.status == "passed":
                bucket["passed"] += 1
            elif enrollment.status == "failed" or enrollment.final_grade in ["F", "NP"]:
                bucket["failed"] += 1
            else:
                bucket["in_progress"] += 1

        context["sections"] = sections
        context["pending_requests"] = pending_requests.prefetch_related("logs")
        context["enrollments"] = enrollments
        analytics = (
            Enrollment.objects.filter(section__in=sections, final_grade__isnull=False)
            .values("section_id")
            .annotate(
                avg_grade=Avg("final_grade"),
                max_grade=Max("final_grade"),
                min_grade=Min("final_grade"),
                total=Count("id"),
                pass_count=Count("id", filter=Q(final_grade__gte=60)),
            )
        )
        analytics_map = {item["section_id"]: item for item in analytics}

        context["grade_overview"] = [
            {
                "section": section,
                "passed": per_section_counts[section.id]["passed"],
                "failed": per_section_counts[section.id]["failed"],
                "in_progress": per_section_counts[section.id]["in_progress"],
                "avg": round(analytics_map.get(section.id, {}).get("avg_grade"), 2) if analytics_map.get(section.id, {}).get("avg_grade") is not None else None,
                "max": analytics_map.get(section.id, {}).get("max_grade"),
                "min": analytics_map.get(section.id, {}).get("min_grade"),
                "pass_rate": (round((analytics_map.get(section.id, {}).get("pass_count", 0) / analytics_map.get(section.id, {}).get("total", 1)) * 100, 1)
                               if analytics_map.get(section.id, {}).get("total") else None),
            }
            for section in sections
        ]
        context["schedule"] = MeetingTime.objects.filter(section__in=sections).select_related(
            "section__course", "section__semester"
        )
        context["stats"] = {
            "section_count": len(sections),
            "pending_count": pending_requests.count(),
            "enrollment_count": len(enrollments),
        }
        context["profile"] = instructor
        return context


class InstructorProfileView(LoginRequiredMixin, TemplateView):
    template_name = "registration/instructor_profile.html"

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "instructor_profile"):
            return HttpResponseForbidden("仅教师可访问此页面")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = InstructorContactForm(request.POST, instructor=request.user.instructor_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "联系方式已更新。")
            return redirect("instructor_profile")
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.request.user.instructor_profile
        context["form"] = kwargs.get("form") or InstructorContactForm(
            instructor=self.request.user.instructor_profile
        )
        return context


class InstructorRosterView(LoginRequiredMixin, TemplateView):
    template_name = "registration/instructor_roster.html"

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "instructor_profile"):
            return HttpResponseForbidden("仅教师可访问此页面")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instructor = self.request.user.instructor_profile
        sections = (
            CourseSection.objects.filter(instructor=instructor)
            .select_related("course", "semester")
            .prefetch_related("meeting_times")
            .order_by("course__code", "section_number")
        )
        enrollments = (
            Enrollment.objects.filter(section__in=sections)
            .select_related("student__user", "section__course", "section__semester")
            .order_by("section__course__code", "student__user__username")
        )

        roster_map: dict[int, list[Enrollment]] = defaultdict(list)
        for enrollment in enrollments:
            roster_map[enrollment.section_id].append(enrollment)

        context["rosters"] = [
            {"section": section, "enrollments": roster_map.get(section.id, [])}
            for section in sections
        ]
        context["profile"] = instructor
        context["stats"] = {
            "section_count": sections.count(),
            "enrollment_count": enrollments.count(),
        }
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
        context["bulk_form"] = kwargs.get("bulk_form") or AdminBulkEnrollmentForm()
        context["class_schedule_form"] = kwargs.get("class_schedule_form") or AdminClassScheduleForm()

        enrollment_summary = (
            Enrollment.objects.exclude(status="dropped")
            .values("section__course__code", "section__course__name")
            .annotate(
                total=Count("id"),
                passed=Count("id", filter=Q(status="passed") | Q(final_grade__gte=60)),
            )
            .order_by("section__course__code")[:15]
        )
        course_pass_rates = []
        for item in enrollment_summary:
            total = item["total"] or 0
            pass_rate = round((item["passed"] / total) * 100, 1) if total else None
            course_pass_rates.append(
                {
                    "course_code": item["section__course__code"],
                    "course_name": item["section__course__name"],
                    "pass_rate": pass_rate,
                    "total": total,
                }
            )

        gpa_values = []
        students = StudentProfile.objects.prefetch_related("enrollments__section__course")
        for student in students:
            gpa = calculate_gpa_from_enrollments(student.enrollments.all())
            if gpa is not None:
                gpa_values.append(gpa)

        buckets = {"3.5-4.0": 0, "3.0-3.49": 0, "2.0-2.99": 0, "0-1.99": 0}
        for gpa in gpa_values:
            if gpa >= 3.5:
                buckets["3.5-4.0"] += 1
            elif gpa >= 3.0:
                buckets["3.0-3.49"] += 1
            elif gpa >= 2.0:
                buckets["2.0-2.99"] += 1
            else:
                buckets["0-1.99"] += 1

        context["grade_stats"] = {
            "course_pass_rates": course_pass_rates,
            "gpa_distribution": buckets,
            "gpa_sample_size": len(gpa_values),
        }
        return context


class AdminBulkEnrollmentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden("仅管理员可批量分配课程")

        form = AdminBulkEnrollmentForm(request.POST)
        if not form.is_valid():
            return AdminDashboardView.as_view()(request, bulk_form=form)

        section = form.cleaned_data["section"]
        department = form.cleaned_data.get("department")
        class_group = form.cleaned_data.get("class_group")
        major = form.cleaned_data.get("major")

        students = StudentProfile.objects.all()
        if department:
            students = students.filter(department=department)
        if class_group:
            students = students.filter(class_group=class_group)
        if major:
            students = students.filter(major__icontains=major)

        created = 0
        for student in students:
            enrollment, created_flag = Enrollment.objects.update_or_create(
                student=student,
                section=section,
                defaults={"status": "enrolling"},
            )
            created += int(created_flag)

        if created:
            messages.success(
                request,
                f"已为 {created} 名学生批量分配 {section.course.name}（{section.semester.code}）。",
            )
        else:
            messages.info(request, "筛选范围内的学生已存在对应选课记录。")
        return redirect("admin_home")


class AdminClassScheduleView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden("仅管理员可批量分配课程")

        form = AdminClassScheduleForm(request.POST)
        if not form.is_valid():
            return AdminDashboardView.as_view()(request, class_schedule_form=form)

        class_group = form.cleaned_data["class_group"]
        sections = form.cleaned_data["sections"]
        students = StudentProfile.objects.filter(class_group=class_group)

        created = 0
        for student in students:
            for section in sections:
                _, created_flag = Enrollment.objects.update_or_create(
                    student=student,
                    section=section,
                    defaults={"status": "enrolling"},
                )
                created += int(created_flag)

        if created:
            section_labels = ", ".join(
                f"{section.course.name}（{section.semester.code}）" for section in sections
            )
            messages.success(
                request,
                f"已为 {students.count()} 名学生同步班级课表：{section_labels}。新增 {created} 条选课记录。",
            )
        else:
            messages.info(request, "所选班级的学生均已存在对应选课记录。")
        return redirect("admin_home")


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
            request_type__in=["retake", "cross_college", "credit_overload"],
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

        if req_obj.request_type == "retake" and not request.user.is_staff:
            return HttpResponseForbidden("重修申请仅教务管理员可审批")

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

        if decision == "approved" and req_obj.request_type == "retake" and req_obj.section:
            Enrollment.objects.update_or_create(
                student=req_obj.student,
                section=req_obj.section,
                defaults={"status": "enrolling"},
            )
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
        grade_raw = request.POST.get("final_grade")
        status = request.POST.get("status", "enrolling")

        grade = None
        if grade_raw:
            try:
                grade = round(float(grade_raw), 2)
            except ValueError:
                messages.error(request, "成绩格式不正确，请输入数字。")
                return redirect("instructor_home")
            if grade < 0 or grade > 100:
                messages.error(request, "成绩需在 0-100 之间。")
                return redirect("instructor_home")

        try:
            enrollment = Enrollment.objects.get(pk=enrollment_id, section=section)
        except Enrollment.DoesNotExist:
            messages.error(request, "未找到选课记录。")
            return redirect("instructor_home")

        enrollment.final_grade = grade
        if grade is not None:
            enrollment.status = "passed" if grade >= 60 else "failed"
        else:
            enrollment.status = status
        enrollment.grade_points = grade_to_points(grade)
        enrollment.save(update_fields=["final_grade", "status", "grade_points"])
        messages.success(request, "已更新成绩记录。")
        return redirect("instructor_home")


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
