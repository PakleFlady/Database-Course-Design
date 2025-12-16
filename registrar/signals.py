"""Signals to provision default passwords and security flags for users."""
from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from registrar.models import UserSecurityProfile

User = get_user_model()
DEFAULT_INITIAL_PASSWORD = getattr(settings, "DEFAULT_INITIAL_PASSWORD", "ChangeMe123!")


@receiver(post_save, sender=User)
def ensure_default_password_and_policy(sender, instance: User, created: bool, **kwargs):
    profile, _ = UserSecurityProfile.objects.get_or_create(user=instance)

    if created and not instance.has_usable_password():
        instance.set_password(DEFAULT_INITIAL_PASSWORD)
        User.objects.filter(pk=instance.pk).update(password=instance.password)

    if created:
        profile.force_password_change = True
        profile.save(update_fields=["force_password_change", "updated_at"])
