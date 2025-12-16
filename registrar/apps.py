from django.apps import AppConfig


class RegistrarConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "registrar"
    verbose_name = "课程与成绩管理"

    def ready(self) -> None:  # pragma: no cover - Django convention
        from . import signals  # noqa: F401
