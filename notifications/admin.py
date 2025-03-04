from django.contrib import admin

# Register your models here.
# admin.py
from django.contrib import admin
from .models import Notification, NotificationPreference

# Register your models here.

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'title', 'created_at', 'read', 'priority')
    search_fields = ('user__username', 'title', 'message', 'type')
    list_filter = ('type', 'priority', 'read', 'created_at')
    readonly_fields = ('created_at', 'read_at')  # Make these fields read-only in admin


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_enabled', 'push_enabled', 'sms_enabled', 'quiet_hours_start', 'quiet_hours_end')
    search_fields = ('user__username',)
    list_filter = ('email_enabled', 'push_enabled', 'sms_enabled')