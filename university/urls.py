"""URL configuration for university project."""
from django.contrib import admin
from django.urls import path

from registrar.views import (
    AccountHomeView,
    AdminBulkEnrollmentView,
    ForcePasswordChangeDoneView,
    ForcePasswordChangeView,
    InstructorLoginView,
    LoginPortalView,
    StudentEnrollmentView,
    AdminDashboardView,
    ApprovalDecisionView,
    ApprovalQueueView,
    StudentLoginView,
    StudentDashboardView,
    StudentScheduleExportView,
    InstructorScheduleExportView,
    InstructorDashboardView,
    InstructorSectionDetailView,
    UserLogoutView,
    InstructorGradeUpdateView,
    AdminSectionLockToggleView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", LoginPortalView.as_view(), name="login_portal"),
    path("accounts/login/student/", StudentLoginView.as_view(), name="student_login"),
    path(
        "accounts/login/instructor/",
        InstructorLoginView.as_view(),
        name="instructor_login",
    ),
    path("accounts/logout/", UserLogoutView.as_view(), name="logout"),
    path("accounts/home/", AccountHomeView.as_view(), name="account_home"),
    path("accounts/home/student/", StudentDashboardView.as_view(), name="student_home"),
    path(
        "accounts/home/student/enrollment/",
        StudentEnrollmentView.as_view(),
        name="student_enrollment",
    ),
    path(
        "accounts/home/student/schedule/export/",
        StudentScheduleExportView.as_view(),
        name="student_schedule_export",
    ),
    path("accounts/home/instructor/", InstructorDashboardView.as_view(), name="instructor_home"),
    path(
        "accounts/home/instructor/schedule/export/",
        InstructorScheduleExportView.as_view(),
        name="instructor_schedule_export",
    ),
    path(
        "accounts/home/instructor/sections/<int:section_id>/",
        InstructorSectionDetailView.as_view(),
        name="instructor_section_detail",
    ),
    path(
        "accounts/home/instructor/sections/<int:section_id>/grade/",
        InstructorGradeUpdateView.as_view(),
        name="grade_update",
    ),
    path("accounts/home/admin/", AdminDashboardView.as_view(), name="admin_home"),
    path("accounts/home/admin/bulk-enroll/", AdminBulkEnrollmentView.as_view(), name="admin_bulk_enroll"),
    path(
        "accounts/home/admin/sections/<int:section_id>/lock/",
        AdminSectionLockToggleView.as_view(),
        name="section_lock_toggle",
    ),
    path("accounts/password-change/", ForcePasswordChangeView.as_view(), name="force_password_change"),
    path(
        "accounts/password-change/done/",
        ForcePasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path("approvals/", ApprovalQueueView.as_view(), name="approval_queue"),
    path("approvals/<int:pk>/", ApprovalDecisionView.as_view(), name="approval_decision"),
]
