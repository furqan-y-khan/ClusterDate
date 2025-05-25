from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from model_utils import Choices
from jsonfield.fields import JSONField
from swapper import swappable_setting


class NotificationQuerySet(models.query.QuerySet):
    """Notification QuerySet Manager methods"""

    def unsent(self):
        return self.filter(emailed=False)

    def sent(self):
        return self.filter(emailed=True)

    def unread(self, include_deleted=False):
        """Return only unread items in the current queryset"""
        if include_deleted:
            return self.filter(unread=True)
        else:
            return self.filter(unread=True, deleted=False)

    def read(self, include_deleted=False):
        """Return only read items in the current queryset"""
        if include_deleted:
            return self.filter(unread=False)
        else:
            return self.filter(unread=False, deleted=False)

    def mark_all_as_read(self, recipient=None):
        """Mark as read any unread messages in the current queryset.

        Optionally, filter these by recipient first.
        """
        # We want to filter out read ones, as later we will store
        # the time they were marked as read.
        qset = self.unread(True)
        if recipient:
            qset = qset.filter(recipient=recipient)

        return qset.update(unread=False)

    def mark_all_as_unread(self, recipient=None):
        """Mark as unread any read messages in the current queryset.

        Optionally, filter these by recipient first.
        """
        qset = self.read(True)

        if recipient:
            qset = qset.filter(recipient=recipient)

        return qset.update(unread=True)

    def deleted(self):
        """Return only deleted items in the current queryset"""
        return self.filter(deleted=True)

    def active(self):
        """Return only active(not deleted) items in the current queryset"""
        return self.filter(deleted=False)

    def mark_all_as_deleted(self, recipient=None):
        """Mark current queryset as deleted.
        Optionally, filter by recipient first.
        """
        qset = self.active()
        if recipient:
            qset = qset.filter(recipient=recipient)

        return qset.update(deleted=True)

    def mark_all_as_active(self, recipient=None):
        """Mark current queryset as active(not deleted).
        Optionally, filter by recipient first.
        """
        qset = self.deleted()
        if recipient:
            qset = qset.filter(recipient=recipient)

        return qset.update(deleted=False)

    def mark_as_unsent(self, recipient=None):
        qset = self.sent()
        if recipient:
            qset = qset.filter(recipient=recipient)
        return qset.update(emailed=False)

    def mark_as_sent(self, recipient=None):
        qset = self.unsent()
        if recipient:
            qset = qset.filter(recipient=recipient)
        return qset.update(emailed=True)


class AbstractNotification(models.Model):
    """
    Django Notification abstract model
    """
    LEVELS = Choices('success', 'info', 'warning', 'error')
    level = models.CharField(_('level'), choices=LEVELS, default=LEVELS.info, max_length=20)

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications_fix',
        verbose_name=_('recipient'),
        blank=False,
    )
    unread = models.BooleanField(_('unread'), default=True, blank=False, db_index=True)

    actor_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='notify_actor',
        verbose_name=_('actor content type')
    )
    actor_object_id = models.CharField(_('actor object id'), max_length=255)
    actor = GenericForeignKey('actor_content_type', 'actor_object_id')

    verb = models.CharField(_('verb'), max_length=255)
    description = models.TextField(_('description'), blank=True, null=True)

    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='notify_target',
        verbose_name=_('target content type'),
        blank=True,
        null=True
    )
    target_object_id = models.CharField(_('target object id'), max_length=255, blank=True, null=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')

    action_object_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='notify_action_object',
        verbose_name=_('action object content type'),
        blank=True,
        null=True
    )
    action_object_object_id = models.CharField(_('action object object id'), max_length=255, blank=True, null=True)
    action_object = GenericForeignKey('action_object_content_type', 'action_object_object_id')

    timestamp = models.DateTimeField(_('timestamp'), default=timezone.now, db_index=True)

    public = models.BooleanField(_('public'), default=True, db_index=True)
    deleted = models.BooleanField(_('deleted'), default=False, db_index=True)
    emailed = models.BooleanField(_('emailed'), default=False, db_index=True)

    data = JSONField(_('data'), blank=True, null=True)

    objects = NotificationQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ('-timestamp',)
        # Using indexes instead of index_together for Django 5.x compatibility
        indexes = [
            models.Index(fields=['recipient', 'unread']),
        ]
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')


class Notification(AbstractNotification):
    class Meta(AbstractNotification.Meta):
        swappable = swappable_setting('notifications', 'Notification') 