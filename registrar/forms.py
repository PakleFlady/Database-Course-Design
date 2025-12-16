"""Forms for admin helpers and self-service flows."""
from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

from .models import CourseSection, Department, StudentProfile, StudentRequest, UserSecurity

User = get_user_model()


class _RoleAuthenticationForm(AuthenticationForm):
    """Base form enforcing that a user matches the expected role."""

    expected_role: str | None = None

    def confirm_login_allowed(self, user):  # pragma: no cover - form hook
        super().confirm_login_allowed(user)
        if self.expected_role == "student" and not hasattr(user, "student_profile"):
            raise forms.ValidationError("请使用学生账号登录此入口。", code="invalid_login")
        if self.expected_role == "instructor" and not hasattr(user, "instructor_profile"):
            raise forms.ValidationError("请使用教师账号登录此入口。", code="invalid_login")


class StudentAuthenticationForm(_RoleAuthenticationForm):
    expected_role = "student"


class InstructorAuthenticationForm(_RoleAuthenticationForm):
    expected_role = "instructor"


class UserCreationWithProfileForm(forms.ModelForm):
    """Assign default password and create student/teacher profiles when needed."""

    ROLE_CHOICES = [
        ("student", "学生"),
        ("instructor", "教师"),
        ("staff", "仅管理员/工作人员"),
    ]

    role = forms.ChoiceField(label="账号角色", choices=ROLE_CHOICES, initial="student")
    department = forms.ModelChoiceField(
        label="所属院系", queryset=Department.objects.all(), required=False
    )
    college = forms.CharField(label="学院", required=False)
    major = forms.CharField(label="专业", required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_superuser",
            "is_active",
            "groups",
            "user_permissions",
        )

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        department = cleaned.get("department")
        college = cleaned.get("college")
        major = cleaned.get("major")

        if role == "instructor" and not department:
            raise forms.ValidationError("创建教师账号时必须选择所属院系。")
        if role == "student" and (not college or not major):
            raise forms.ValidationError("创建学生账号时需填写学院与专业。")
        return cleaned

    def save(self, commit: bool = True):
        from django.conf import settings

        user = super().save(commit=False)
        user.set_password(settings.DEFAULT_INITIAL_PASSWORD)
        if commit:
            user.save()
            self.save_m2m()

            role = self.cleaned_data.get("role")
            department = self.cleaned_data.get("department")
            college = self.cleaned_data.get("college")
            major = self.cleaned_data.get("major")

            if role == "instructor" and department:
                from .models import InstructorProfile

                InstructorProfile.objects.create(user=user, department=department)
            elif role == "student" and college and major:
                StudentProfile.objects.create(user=user, college=college, major=major)

            security, _ = UserSecurity.objects.get_or_create(user=user)
            if user.is_staff or user.is_superuser:
                security.must_change_password = False
                security.save(update_fields=["must_change_password"])
        return user


class SelfServiceRequestForm(forms.ModelForm):
    class Meta:
        model = StudentRequest
        fields = ["request_type", "section", "reason"]
        labels = {
            "request_type": "办理事项",
            "section": "关联教学班",
            "reason": "说明/备注",
        }
        widgets = {"reason": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, student=None, **kwargs):
        self.student = student
        super().__init__(*args, **kwargs)
        self.fields["section"].queryset = CourseSection.objects.select_related("course", "semester").all()
        self.fields["section"].required = False

    def clean(self):
        cleaned = super().clean()
        request_type = cleaned.get("request_type")
        section = cleaned.get("section")
        if request_type in {"enroll", "drop", "retake", "cross_college"} and not section:
            raise forms.ValidationError("请选择要办理的教学班。")
        if not self.student:
            raise forms.ValidationError("仅学生账号可提交申请。")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.student = self.student
        if commit:
            obj.save()
        return obj


class ApprovalDecisionForm(forms.Form):
    DECISIONS = [
        ("approved", "通过"),
        ("rejected", "驳回"),
    ]

    decision = forms.ChoiceField(label="审批结果", choices=DECISIONS)
    note = forms.CharField(label="审核意见", required=False, widget=forms.Textarea)


class AdminBulkEnrollmentForm(forms.Form):
    section = forms.ModelChoiceField(label="教学班", queryset=CourseSection.objects.select_related("course", "semester"))
    college = forms.CharField(label="学院", required=False)
    major = forms.CharField(label="班级/专业", required=False)

    def clean(self):
        cleaned = super().clean()
        college = cleaned.get("college")
        major = cleaned.get("major")
        if not college and not major:
            raise forms.ValidationError("请至少填写学院或班级条件。")
        return cleaned
