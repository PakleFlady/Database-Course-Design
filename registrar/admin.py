"""Admin configuration for the course registration domain."""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .forms import UserCreationWithProfileForm
from .models import (
    ApprovalLog,
    Course,
    CoursePrerequisite,
    CourseSection,
    Department,
    Enrollment,
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
                    "college",
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


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "credits", "course_type", "department")
    list_filter = ("course_type", "department")
    search_fields = ("code", "name")


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
    list_display = ("user", "major", "college")
    search_fields = ("user__username", "major", "college")


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "title")
    list_filter = ("department",)
    search_fields = ("user__username", "title")


@admin.register(CoursePrerequisite)
class CoursePrerequisiteAdmin(admin.ModelAdmin):
    list_display = ("course", "prerequisite", "min_grade")
    search_fields = ("course__code", "prerequisite__code")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "start_date", "end_date")
    list_filter = ("start_date",)
    search_fields = ("code", "name")
