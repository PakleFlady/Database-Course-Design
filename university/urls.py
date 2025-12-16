"""URL configuration for university project."""
from django.contrib import admin
from django.urls import path

from registrar.views import (
    AccountHomeView,
    ForcePasswordChangeDoneView,
    ForcePasswordChangeView,
    InstructorLoginView,
    LoginPortalView,
    StudentLoginView,
    UserLogoutView,
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
    path("accounts/password-change/", ForcePasswordChangeView.as_view(), name="force_password_change"),
    path(
        "accounts/password-change/done/",
        ForcePasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
]
