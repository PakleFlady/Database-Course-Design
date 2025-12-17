"""Django models for the course registration and grade management domain."""
from __future__ import annotations

import datetime

from django.core.exceptions import ValidationError

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F, Q, Max

User = get_user_model()


class UserSecurity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="security", verbose_name="账号")
    must_change_password = models.BooleanField("首次登录需修改密码", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "账号安全设置"
        verbose_name_plural = "账号安全设置"

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        return f"Security settings for {self.user.username}"


class Department(models.Model):
    code = models.CharField("院系代码", max_length=20, unique=True)
    name = models.CharField("院系名称", max_length=255)
    numeric_code = models.PositiveSmallIntegerField(
        "院系编号", unique=True, null=True, blank=True
    )

    class Meta:
        verbose_name = "院系"
        verbose_name_plural = "院系"
        ordering = ["code"]

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        numeric = f"#{self.numeric_code}" if self.numeric_code is not None else "未编号"
        return f"{self.code} ({numeric}) - {self.name}"

    def assign_numeric_code(self) -> int:
        """Ensure the department has an auto-incrementing numeric code."""

        if self.numeric_code is None:
            current_max = Department.objects.aggregate(max_code=Max("numeric_code")).get("max_code") or 0
            self.numeric_code = current_max + 1
        return int(self.numeric_code)

    def save(self, *args, **kwargs):
        self.assign_numeric_code()
        super().save(*args, **kwargs)


class Semester(models.Model):
    code = models.CharField("学期代码", max_length=20, unique=True)
    name = models.CharField("学期名称", max_length=255)
    start_date = models.DateField("开始日期")
    end_date = models.DateField("结束日期")

    class Meta:
        verbose_name = "学期"
        verbose_name_plural = "学期"
        ordering = ["-start_date"]

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        return f"{self.code} ({self.name})"


class Course(models.Model):
    COURSE_TYPE_CHOICES = [
        ("general_required", "通识必修"),
        ("major_required", "专业必修"),
        ("major_elective", "专业选修"),
        ("university_elective", "校级选修"),
        ("practical", "实践/实验"),
    ]

    code = models.CharField("课程代码", max_length=20, unique=True)
    name = models.CharField("课程名称", max_length=255)
    credits = models.DecimalField("学分", max_digits=4, decimal_places=1)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="courses", verbose_name="开课院系")
    course_type = models.CharField("课程类别", max_length=50, choices=COURSE_TYPE_CHOICES)
    description = models.TextField("课程简介", blank=True)

    class Meta:
        verbose_name = "课程"
        verbose_name_plural = "课程"
        ordering = ["code"]

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        return f"{self.code} - {self.name}"


class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="instructor_profile", verbose_name="账号")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="instructors", verbose_name="所属院系")
    title = models.CharField("职称", max_length=100, blank=True)
    office_phone = models.CharField("办公电话", max_length=50, blank=True)

    class Meta:
        verbose_name = "教师"
        verbose_name_plural = "教师"
        ordering = ["user__username"]

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        return f"{self.user.get_full_name() or self.user.username} ({self.department.code})"

    def clean(self):
        super().clean()
        if not self.pk:
            return
        try:
            original = InstructorProfile.objects.get(pk=self.pk)
        except InstructorProfile.DoesNotExist:
            return
        if original.department_id != self.department_id:
            raise ValidationError("教师所属院系不可自行修改，请联系管理员。")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ClassGroup(models.Model):
    name = models.CharField("班级名称", max_length=100)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="class_groups", verbose_name="所属学院")

    class Meta:
        verbose_name = "班级"
        verbose_name_plural = "班级"
        unique_together = [("name", "department")]
        ordering = ["department__code", "name"]

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        return f"{self.department.code}-{self.name}"


class StudentProfile(models.Model):
    GENDER_CHOICES = [
        ("male", "男"),
        ("female", "女"),
        ("other", "其他"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile", verbose_name="账号")
    gender = models.CharField("性别", max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField("出生日期", null=True, blank=True)
    contact_email = models.EmailField("联系邮箱", blank=True)
    contact_phone = models.CharField("联系电话", max_length=50, blank=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="students",
        verbose_name="学院",
        null=True,
        blank=True,
    )
    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.PROTECT,
        related_name="students",
        verbose_name="班级",
        null=True,
        blank=True,
    )
    major = models.CharField("专业", max_length=255)
    student_number = models.CharField("学号", max_length=32, unique=True, null=True, blank=True)

    class Meta:
        verbose_name = "学生"
        verbose_name_plural = "学生"
        ordering = ["student_number", "user__username"]

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        return f"{self.user.get_full_name() or self.user.username} - {self.major}"

    @classmethod
    def generate_student_number(cls, department: Department) -> str:
        """Generate a student number in the format <year><dept_numeric><seq>."""

        if department.numeric_code is None:
            department.assign_numeric_code()
            if department.pk:
                department.save(update_fields=["numeric_code"])

        year_prefix = datetime.date.today().year
        dept_code = f"{int(department.numeric_code):03d}"
        base_prefix = f"{year_prefix}{dept_code}"
        last_number = (
            cls.objects.filter(student_number__startswith=base_prefix)
            .order_by("-student_number")
            .values_list("student_number", flat=True)
            .first()
        )
        if last_number and last_number[-3:].isdigit():
            sequence = int(last_number[-3:]) + 1
        else:
            sequence = 1
        return f"{base_prefix}{sequence:03d}"

    def save(self, *args, **kwargs):
        if not self.student_number and self.department:
            self.student_number = self.generate_student_number(self.department)
        super().save(*args, **kwargs)


class CourseSection(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections", verbose_name="课程")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="sections", verbose_name="学期")
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.PROTECT, related_name="sections", verbose_name="教师")
    section_number = models.PositiveSmallIntegerField("教学班号", default=1)
    capacity = models.PositiveIntegerField("容量", default=60)
    grades_locked = models.BooleanField("成绩填报锁定", default=False)
    notes = models.TextField("备注", blank=True)

    class Meta:
        verbose_name = "教学班"
        verbose_name_plural = "教学班"
        unique_together = [("course", "semester", "section_number")]
        ordering = ["course__code", "section_number"]

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        return f"{self.course.code}-S{self.section_number} ({self.semester.code})"


class MeetingTime(models.Model):
    DAY_OF_WEEK_CHOICES = [
        (1, "周一"),
        (2, "周二"),
        (3, "周三"),
        (4, "周四"),
        (5, "周五"),
        (6, "周六"),
        (7, "周日"),
    ]

    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name="meeting_times", verbose_name="教学班")
    day_of_week = models.PositiveSmallIntegerField("周次", choices=DAY_OF_WEEK_CHOICES)
    start_time = models.TimeField("开始时间")
    end_time = models.TimeField("结束时间")
    location = models.CharField("上课地点", max_length=255)

    class Meta:
        verbose_name = "上课时间"
        verbose_name_plural = "上课时间"
        ordering = ["day_of_week", "start_time"]
        constraints = [
            models.CheckConstraint(
                check=Q(end_time__gt=F("start_time")),
                name="meetingtime_end_after_start",
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        return f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time} ({self.location})"

    def clean(self):
        super().clean()
        if not self.section_id:
            return
        instructor = self.section.instructor
        overlap_exists = MeetingTime.objects.filter(
            section__instructor=instructor,
            day_of_week=self.day_of_week,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        ).exclude(pk=self.pk).exists()
        if overlap_exists:
            raise ValidationError("该教师在该时间段已有其它课程，无法排课。")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class CoursePrerequisite(models.Model):
    GRADE_CHOICES = [
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
        ("F", "F"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="prerequisites", verbose_name="课程")
    prerequisite = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="required_for", verbose_name="先修课")
    min_grade = models.CharField("最低成绩", max_length=2, choices=GRADE_CHOICES, default="C")

    class Meta:
        verbose_name = "先修要求"
        verbose_name_plural = "先修要求"
        unique_together = [("course", "prerequisite")]
        ordering = ["course__code", "prerequisite__code"]

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        return f"{self.course.code} requires {self.prerequisite.code} (>= {self.min_grade})"


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ("enrolling", "选课中"),
        ("dropped", "已退课"),
        ("passed", "已通过"),
        ("failed", "未通过"),
    ]
    GRADE_CHOICES = [
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
        ("F", "F"),
        ("P", "P"),
        ("NP", "NP"),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="enrollments", verbose_name="学生")
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name="enrollments", verbose_name="教学班")
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default="enrolling")
    final_grade = models.CharField("最终成绩", max_length=2, choices=GRADE_CHOICES, blank=True)
    grade_points = models.DecimalField("绩点", max_digits=4, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "选课记录"
        verbose_name_plural = "选课记录"
        unique_together = [("student", "section")]
        ordering = ["section__semester__start_date", "student__user__username"]

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        return f"{self.student} -> {self.section} ({self.status})"


class StudentRequest(models.Model):
    REQUEST_TYPE_CHOICES = [
        ("enroll", "报名/选课"),
        ("drop", "退课申请"),
        ("retake", "重修申请"),
        ("cross_college", "跨院选课审批"),
        ("credit_overload", "超学分申请"),
    ]

    STATUS_CHOICES = [
        ("pending", "待审批"),
        ("approved", "已通过"),
        ("rejected", "已驳回"),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="requests",
        verbose_name="学生",
    )
    section = models.ForeignKey(
        CourseSection,
        on_delete=models.SET_NULL,
        related_name="requests",
        null=True,
        blank=True,
        verbose_name="教学班",
    )
    request_type = models.CharField("申请类型", max_length=32, choices=REQUEST_TYPE_CHOICES)
    reason = models.TextField("申请原因", blank=True)
    status = models.CharField("审批状态", max_length=16, choices=STATUS_CHOICES, default="pending")
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handled_requests",
        verbose_name="审核人",
    )
    reviewed_at = models.DateTimeField("审核时间", null=True, blank=True)
    metadata = models.JSONField("附加信息", default=dict, blank=True)
    created_at = models.DateTimeField("提交时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "学生自助申请"
        verbose_name_plural = "学生自助申请"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        return f"{self.get_request_type_display()} - {self.student} ({self.get_status_display()})"

    def requires_approval(self) -> bool:
        return self.request_type in {"retake", "cross_college", "credit_overload"}


class ApprovalLog(models.Model):
    ACTION_CHOICES = [
        ("approved", "通过"),
        ("rejected", "驳回"),
    ]

    request = models.ForeignKey(
        StudentRequest,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name="申请",
    )
    action = models.CharField("操作", max_length=16, choices=ACTION_CHOICES)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approval_logs",
        verbose_name="执行人",
    )
    note = models.TextField("审核意见", blank=True)
    created_at = models.DateTimeField("时间", auto_now_add=True)

    class Meta:
        verbose_name = "审批日志"
        verbose_name_plural = "审批日志"
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        return f"{self.request} -> {self.get_action_display()}"
