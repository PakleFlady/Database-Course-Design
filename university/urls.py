"""URL configuration for university project."""
from django.contrib import admin
from django.urls import path

from registrar.views import EnforcedPasswordChangeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/password_change/", EnforcedPasswordChangeView.as_view(), name="password_change"),
    path(
        "accounts/password_change/done/",
        admin.site.password_change_done,
        name="password_change_done",
    ),
]
