import uuid

import requests
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('Title'), max_length=255, unique=True)
    description = models.TextField(_('Description'), blank=False, null=False)
    body = models.TextField(_('Message body'), blank=False, null=False)
    created_at = models.DateTimeField(
        auto_now=True, verbose_name=_('Created at'), db_index=True
    )

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        db_table = 'notifications'

    def __str__(self):
        return self.title


def on_notification_save(sender, instance, **kwargs):
    if kwargs['created']:
        requests.post(
            f'{settings.NOTIFICATION_API_URL}/to-all',
            json={'body': instance.body}
        )


post_save.connect(on_notification_save, sender=Notification)
