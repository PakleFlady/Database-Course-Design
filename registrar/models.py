"""Django models for the course registration and grade management domain."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F, Q

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

    class Meta:
        verbose_name = "院系"
        verbose_name_plural = "院系"
        ordering = ["code"]

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        return f"{self.code} - {self.name}"


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
    college = models.CharField("学院", max_length=255)
    major = models.CharField("专业", max_length=255)

    class Meta:
        verbose_name = "学生"
        verbose_name_plural = "学生"
        ordering = ["user__username"]

    def __str__(self) -> str:  # pragma: no cover - human readable labels
        return f"{self.user.get_full_name() or self.user.username} - {self.major}"


class CourseSection(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections", verbose_name="课程")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="sections", verbose_name="学期")
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.PROTECT, related_name="sections", verbose_name="教师")
    section_number = models.PositiveSmallIntegerField("教学班号", default=1)
    capacity = models.PositiveIntegerField("容量", default=60)
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
        ("waitlisted", "候补"),
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
