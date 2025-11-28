from django.contrib import admin
from . import models


@admin.register(models.College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(models.Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "college")
    list_filter = ("college",)
    search_fields = ("code", "name")


@admin.register(models.Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "department")
    list_filter = ("department",)
    search_fields = ("code", "name")


@admin.register(models.Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "full_name", "department", "email")
    list_filter = ("department", "gender")
    search_fields = ("employee_id", "full_name", "email")


@admin.register(models.Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "full_name", "college", "major", "email")
    list_filter = ("college", "major", "gender")
    search_fields = ("student_id", "full_name", "email")


@admin.register(models.Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date")
    search_fields = ("name", "code")


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("course_code", "name", "credits", "department", "course_type")
    list_filter = ("department", "course_type")
    search_fields = ("course_code", "name")


@admin.register(models.CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = (
        "course",
        "section_code",
        "semester",
        "instructor",
        "weekday",
        "start_time",
        "end_time",
        "capacity",
    )
    list_filter = ("semester", "instructor", "weekday")
    search_fields = ("course__course_code", "course__name", "section_code")


@admin.register(models.CoursePrerequisite)
class CoursePrerequisiteAdmin(admin.ModelAdmin):
    list_display = ("course", "prerequisite", "min_grade")
    search_fields = (
        "course__course_code",
        "course__name",
        "prerequisite__course_code",
        "prerequisite__name",
    )


@admin.register(models.Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "section",
        "status",
        "final_grade",
        "grade_points",
    )
    list_filter = ("status", "section__semester")
    search_fields = (
        "student__student_id",
        "student__full_name",
        "section__course__course_code",
        "section__course__name",
    )
    autocomplete_fields = ("student", "section")
