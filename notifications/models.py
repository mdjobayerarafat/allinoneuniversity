from django.db import models

# Create your models here.
# models.py
from django.db import models


class Notification(models.Model):
    TYPES = (
        ('system', 'System Notification'),
        ('academic', 'Academic Notification'),
        ('event', 'Event Notification'),
        ('transport', 'Transportation Alert'),
        ('cafeteria', 'Cafeteria Notification'),
    )

    PRIORITIES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITIES, default='medium')
    action_url = models.CharField(max_length=255, blank=True)  # URL to navigate to when clicked
    related_object_type = models.CharField(max_length=50, blank=True)  # For polymorphic relations
    related_object_id = models.PositiveIntegerField(null=True, blank=True)


class NotificationPreference(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='notification_preferences')
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    preferences_by_type = models.JSONField(default=dict)  # Detailed preferences for each notification type