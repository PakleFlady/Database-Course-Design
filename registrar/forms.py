"""Forms for admin helpers and self-service flows."""
from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import (
    ClassGroup,
    CourseSection,
    Department,
    InstructorProfile,
    StudentProfile,
    StudentRequest,
    UserSecurity,
)

User = get_user_model()


MAJOR_OPTIONS = {
    "CSE": ["软件工程", "计算机科学与技术", "人工智能", "网络安全", "数据科学"],
    "MATH": ["数学与应用数学", "统计学", "金融数学"],
    "EE": ["电子信息工程", "通信工程", "智能感知"],
    "BUS": ["信息管理与信息系统", "工商管理", "金融科技"],
}


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
    class_group = forms.ModelChoiceField(label="班级", queryset=None, required=False)
    major = forms.ChoiceField(label="专业", required=False, choices=[])

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_group"].queryset = ClassGroup.objects.select_related("department")
        dept_value = None
        data = self.data or None
        if data and data.get("department"):
            try:
                dept_value = Department.objects.get(pk=data.get("department"))
            except Department.DoesNotExist:
                dept_value = None
        if not dept_value and self.initial.get("department"):
            dept_value = self.initial["department"]

        if dept_value:
            self.fields["class_group"].queryset = ClassGroup.objects.filter(department=dept_value)
            self._set_major_choices(dept_value)
        else:
            all_majors = sorted({major for majors in MAJOR_OPTIONS.values() for major in majors})
            self.fields["major"].choices = [("", "请选择专业")] + [(major, major) for major in all_majors]

    def _set_major_choices(self, department):
        if department and department.code in MAJOR_OPTIONS:
            choices = [(m, m) for m in MAJOR_OPTIONS[department.code]]
        else:
            choices = []
        self.fields["major"].choices = [("", "请选择专业")] + choices

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        department = cleaned.get("department")
        class_group = cleaned.get("class_group")
        major = cleaned.get("major")

        if role == "instructor" and not department:
            raise forms.ValidationError("创建教师账号时必须选择所属院系。")
        if role == "student" and (not department or not major):
            raise forms.ValidationError("创建学生账号时需填写学院与专业。")
        if role == "student" and department:
            self._set_major_choices(department)
            if major and major not in dict(self.fields["major"].choices):
                raise forms.ValidationError("请选择所属院系下的专业。")
        if class_group and class_group.department != department:
            raise forms.ValidationError("班级必须隶属于所选学院。")
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
            class_group = self.cleaned_data.get("class_group")
            major = self.cleaned_data.get("major")

            if role == "instructor" and department:
                from .models import InstructorProfile

                InstructorProfile.objects.create(user=user, department=department)
            elif role == "student" and department and major:
                StudentProfile.objects.create(
                    user=user, department=department, class_group=class_group, major=major
                )

            security, _ = UserSecurity.objects.get_or_create(user=user)
            if user.is_staff or user.is_superuser:
                security.must_change_password = False
                security.save(update_fields=["must_change_password"])
        return user


class AccountRegistrationForm(forms.Form):
    ROLE_CHOICES = [
        ("student", "学生"),
        ("instructor", "教师"),
    ]

    username = forms.CharField(label="用户名", max_length=150)
    first_name = forms.CharField(label="姓名", required=False)
    email = forms.EmailField(label="邮箱", required=False)
    password1 = forms.CharField(label="密码", widget=forms.PasswordInput)
    password2 = forms.CharField(label="确认密码", widget=forms.PasswordInput)
    role = forms.ChoiceField(label="注册角色", choices=ROLE_CHOICES)
    department = forms.ModelChoiceField(label="所属院系", queryset=Department.objects.all(), required=False)
    class_group = forms.ModelChoiceField(label="班级", queryset=ClassGroup.objects.select_related("department"), required=False)
    major = forms.ChoiceField(label="专业", required=False, choices=[])

    def _set_major_choices(self, department):
        if department and department.code in MAJOR_OPTIONS:
            choices = [(m, m) for m in MAJOR_OPTIONS[department.code]]
        else:
            # fallback
            choices = [("", "请选择专业")]
        self.fields["major"].choices = [("", "请选择专业")] + choices

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get("username")
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        role = cleaned.get("role")
        department = cleaned.get("department")
        class_group = cleaned.get("class_group")
        major = cleaned.get("major")

        if username and get_user_model().objects.filter(username=username).exists():
            raise ValidationError("该用户名已被注册，请更换后重试。")
        if password1 and password2 and password1 != password2:
            raise ValidationError("两次输入的密码不一致。")
        if role == "instructor" and not department:
            raise ValidationError("教师注册需选择所属院系，提交后等待管理员审批。")
        if role == "student" and (not department or not major):
            raise ValidationError("学生注册需填写所属院系与专业信息。")
        if class_group and department and class_group.department != department:
            raise ValidationError("班级必须属于所选院系。")
        if role == "student" and department:
            self._set_major_choices(department)
            if major and major not in dict(self.fields["major"].choices):
                raise ValidationError("请选择所属院系下的专业。")
        if role == "instructor":
            cleaned["class_group"] = None
            cleaned["major"] = ""
        return cleaned

    def save(self):
        UserModel = get_user_model()
        data = self.cleaned_data
        user = UserModel.objects.create(
            username=data["username"],
            first_name=data.get("first_name", ""),
            email=data.get("email", ""),
            is_active=data["role"] != "instructor",  # 教师账号需管理员审批后激活
        )
        user.set_password(data["password1"])
        user.save()

        security, _ = UserSecurity.objects.get_or_create(user=user)
        security.must_change_password = True
        security.save(update_fields=["must_change_password"])

        if data["role"] == "instructor":
            InstructorProfile.objects.create(user=user, department=data["department"])
        else:
            StudentProfile.objects.create(
                user=user,
                department=data["department"],
                class_group=data.get("class_group"),
                major=data.get("major", ""),
            )
        return user


class StudentContactForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ["contact_email", "contact_phone"]
        labels = {"contact_email": "联系邮箱", "contact_phone": "联系电话"}


class InstructorContactForm(forms.Form):
    email = forms.EmailField(label="邮箱", required=False)
    office_phone = forms.CharField(label="办公电话", required=False)

    def __init__(self, *args, instructor=None, **kwargs):
        self.instructor = instructor
        initial = {}
        if instructor:
            initial = {
                "email": instructor.user.email,
                "office_phone": instructor.office_phone,
            }
        kwargs.setdefault("initial", initial)
        super().__init__(*args, **kwargs)

    def save(self):
        if not self.instructor:
            return
        data = self.cleaned_data
        user = self.instructor.user
        user.email = data.get("email", "")
        user.save(update_fields=["email"])
        self.instructor.office_phone = data.get("office_phone", "")
        self.instructor.save(update_fields=["office_phone"])
        return self.instructor


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
        allowed_types = {"retake", "cross_college", "credit_overload"}
        self.fields["request_type"].choices = [
            choice for choice in StudentRequest.REQUEST_TYPE_CHOICES if choice[0] in allowed_types
        ]
        queryset = CourseSection.objects.select_related("course", "semester")
        if student and student.department:
            queryset = queryset.filter(course__department=student.department)
        self.fields["section"].queryset = queryset
        self.fields["section"].required = False

    def clean(self):
        cleaned = super().clean()
        request_type = cleaned.get("request_type")
        section = cleaned.get("section")
        if request_type in {"retake", "cross_college"} and not section:
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
    department = forms.ModelChoiceField(
        label="学院", queryset=Department.objects.all(), required=False
    )
    class_group = forms.ModelChoiceField(label="班级", queryset=ClassGroup.objects.select_related("department"), required=False)
    major = forms.CharField(label="班级/专业", required=False)

    def clean(self):
        cleaned = super().clean()
        department = cleaned.get("department")
        class_group = cleaned.get("class_group")
        major = cleaned.get("major")
        if class_group and department and class_group.department != department:
            raise forms.ValidationError("班级必须属于所选学院。")
        if not department and not class_group and not major:
            raise forms.ValidationError("请至少填写学院或班级条件。")
        return cleaned


class AdminClassScheduleForm(forms.Form):
    class_group = forms.ModelChoiceField(
        label="班级", queryset=ClassGroup.objects.select_related("department")
    )
    sections = forms.ModelMultipleChoiceField(
        label="批量同步到班级的教学班",
        queryset=CourseSection.objects.select_related("course", "semester", "instructor__user"),
    )

    def clean(self):
        cleaned = super().clean()
        class_group = cleaned.get("class_group")
        sections = cleaned.get("sections") or []
        if class_group and sections:
            cross_department = [
                section
                for section in sections
                if section.course.department != class_group.department
            ]
            if cross_department:
                raise forms.ValidationError("仅允许将本学院的教学班同步到所选班级。")
        return cleaned


class AdminUserPasswordResetForm(forms.Form):
    user_identifier = forms.CharField(label="用户名或邮箱", max_length=150)

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("user_identifier"):
            raise forms.ValidationError("请填写需要重置密码的账号标识。")
        return cleaned
