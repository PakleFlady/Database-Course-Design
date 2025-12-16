"""Signal handlers for registrar."""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserSecurityProfile

User = get_user_model()


@receiver(post_save, sender=User)
def ensure_security_profile(sender, instance, created, **kwargs):  # pragma: no cover - side effect
    profile, _ = UserSecurityProfile.objects.get_or_create(user=instance)

    if created:
        if not instance.has_usable_password():
            instance.set_password(settings.DEFAULT_INITIAL_PASSWORD)
            instance.save(update_fields=["password"])
        profile.must_change_password = True
        profile.save(update_fields=["must_change_password"])
