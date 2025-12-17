"""Admin configuration for the course registration domain."""
from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .forms import UserCreationWithProfileForm
from .models import (
    ApprovalLog,
    ClassGroup,
    Course,
    CoursePrerequisite,
    CourseSection,
    Department,
    Enrollment,
    ProgramPlan,
    ProgramRequirement,
    InstructorProfile,
    MeetingTime,
    Semester,
    StudentProfile,
    StudentRequest,
)

User = get_user_model()
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = UserCreationWithProfileForm
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "first_name",
                    "last_name",
                    "email",
                    "role",
                    "department",
                    "class_group",
                    "major",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )



class MeetingTimeInline(admin.TabularInline):
    model = MeetingTime
    extra = 0
    fields = ("day_of_week", "start_time", "end_time", "location")


class EnrollMajorActionForm(ActionForm):
    major = forms.CharField(label="专业关键字", required=False)
    department = forms.ModelChoiceField(label="学院", queryset=Department.objects.all(), required=False)


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    fields = ("section", "get_semester", "status", "final_grade", "grade_points")
    readonly_fields = ("get_semester",)
    verbose_name = "选课记录"
    verbose_name_plural = "选课记录"

    @admin.display(description="学期")
    def get_semester(self, obj):
        return obj.section.semester


class StudentRequestInline(admin.TabularInline):
    model = StudentRequest
    extra = 0
    fields = ("request_type", "section", "status", "created_at", "reviewed_by")
    readonly_fields = ("created_at",)
    verbose_name = "学生申请"
    verbose_name_plural = "学生申请"


class CourseSectionInline(admin.TabularInline):
    model = CourseSection
    extra = 0
    fields = ("course", "semester", "section_number", "capacity", "grades_locked")
    readonly_fields = ("section_number",)
    verbose_name = "教学班"
    verbose_name_plural = "教学班"


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = (
        "course",
        "semester",
        "section_number",
        "instructor",
        "capacity",
        "grades_locked",
    )
    list_filter = ("semester", "course__department", "grades_locked")
    search_fields = ("course__code", "course__name", "instructor__user__username")
    inlines = [MeetingTimeInline]
    action_form = EnrollMajorActionForm
    actions = ["enroll_students_by_major"]

    @admin.action(description="为选定专业/学院的学生批量选课（受容量限制）")
    def enroll_students_by_major(self, request, queryset):
        major_keyword = request.POST.get("major")
        department = request.POST.get("department") or None

        if not major_keyword:
            self.message_user(request, "请先在操作表单中填写要批量选课的专业关键字。", level=messages.ERROR)
            return

        students = StudentProfile.objects.all()
        students = students.filter(major__icontains=major_keyword)
        if department:
            students = students.filter(department_id=department)

        if not students.exists():
            self.message_user(request, "未找到匹配的学生。", level=messages.WARNING)
            return

        total_added = 0
        for section in queryset:
            existing_ids = set(
                Enrollment.objects.filter(section=section).values_list("student_id", flat=True)
            )
            available = max(section.capacity - Enrollment.objects.filter(section=section, status="enrolling").count(), 0)
            if available <= 0:
                continue

            candidates = students.exclude(id__in=existing_ids).order_by("student_number", "user__username")
            for student in candidates[:available]:
                Enrollment.objects.create(student=student, section=section, status="enrolling")
                total_added += 1

        if total_added:
            self.message_user(request, f"已成功为 {total_added} 位学生添加选课记录。", level=messages.SUCCESS)
        else:
            self.message_user(request, "未添加新的选课记录（可能由于容量已满或学生已选）。", level=messages.INFO)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "credits", "course_type", "department")
    list_filter = ("course_type", "department")
    search_fields = ("code", "name")


class ProgramRequirementInline(admin.TabularInline):
    model = ProgramRequirement
    extra = 0
    filter_horizontal = ("courses",)


@admin.register(ProgramPlan)
class ProgramPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "major",
        "department",
        "academic_year",
        "is_active",
        "enrollment_start",
        "enrollment_end",
    )
    list_filter = ("department", "is_active", "academic_year")
    search_fields = ("name", "major")
    inlines = [ProgramRequirementInline]


@admin.register(ProgramRequirement)
class ProgramRequirementAdmin(admin.ModelAdmin):
    list_display = (
        "plan",
        "category",
        "required_credits",
        "recommended_term",
        "selection_start",
        "selection_end",
    )
    list_filter = ("category", "plan")
    search_fields = ("plan__name", "plan__major", "courses__name")
    filter_horizontal = ("courses",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "section", "status", "final_grade", "grade_points")
    list_filter = ("status", "section__semester", "section__course")
    search_fields = ("student__user__username", "section__course__code")


@admin.register(StudentRequest)
class StudentRequestAdmin(admin.ModelAdmin):
    list_display = ("student", "request_type", "section", "status", "created_at")
    list_filter = ("request_type", "status")
    search_fields = ("student__user__username", "section__course__code")


@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    list_display = ("request", "action", "actor", "created_at")
    list_filter = ("action",)
    search_fields = ("request__student__user__username",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "student_number", "major", "department", "class_group")
    search_fields = ("user__username", "student_number", "major", "department__name", "class_group__name")
    inlines = [EnrollmentInline, StudentRequestInline]


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "title")
    list_filter = ("department",)
    search_fields = ("user__username", "title")
    inlines = [CourseSectionInline]


@admin.register(CoursePrerequisite)
class CoursePrerequisiteAdmin(admin.ModelAdmin):
    list_display = ("course", "prerequisite", "min_grade")
    search_fields = ("course__code", "prerequisite__code")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "department")
    search_fields = ("name", "department__name", "department__code")


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "start_date", "end_date")
    list_filter = ("start_date",)
    search_fields = ("code", "name")
