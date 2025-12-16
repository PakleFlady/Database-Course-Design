"""Admin configuration for the course registration domain."""
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    Course,
    CoursePrerequisite,
    CourseSection,
    Department,
    Enrollment,
    InstructorProfile,
    MeetingTime,
    Semester,
    StudentProfile,
)

User = get_user_model()
admin.site.unregister(User)


class UserCreationWithDefaultPasswordForm(forms.ModelForm):
    """Assign the project default password automatically when creating users."""

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

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        user.set_password(settings.DEFAULT_INITIAL_PASSWORD)
        if commit:
            user.save()
            self.save_m2m()
        return user


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = UserCreationWithDefaultPasswordForm
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
    list_display = ("course", "semester", "section_number", "instructor", "capacity")
    list_filter = ("semester", "course__department")
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
