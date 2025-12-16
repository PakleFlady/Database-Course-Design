"""Signals for default password assignment and security profile bootstrap."""
from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserSecurity

User = get_user_model()


@receiver(post_save, sender=User)
def ensure_security_profile(sender, instance: User, created: bool, **kwargs):
    security, created_security = UserSecurity.objects.get_or_create(user=instance)

    if created and not instance.has_usable_password():
        instance.set_password(getattr(settings, "DEFAULT_INITIAL_PASSWORD", "12345678"))
        instance.save(update_fields=["password"])

    if created_security and not security.must_change_password:
        security.must_change_password = not (instance.is_superuser or instance.is_staff)
        security.save(update_fields=["must_change_password"])
