"""URL configuration for university project."""
from django.contrib import admin
from django.urls import path

from registrar.views import ForcePasswordChangeDoneView, ForcePasswordChangeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/password-change/", ForcePasswordChangeView.as_view(), name="force_password_change"),
    path(
        "accounts/password-change/done/",
        ForcePasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
]
