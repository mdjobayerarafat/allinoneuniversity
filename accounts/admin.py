# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Customize the UserAdmin to display additional fields
class CustomUserAdmin(UserAdmin):
    # Fields to display in the list view
    list_display = ('username', 'email', 'role', 'student_id', 'department', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'student_id', 'department__name')

    # Fieldsets for the add/edit form
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'profile_picture')}),
        ('Role and Department', {'fields': ('role', 'student_id', 'department')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Preferences', {'fields': ('preferences',)}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fieldsets for the add form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'student_id', 'department'),
        }),
    )

# Register the User model with the custom admin class
admin.site.register(User, CustomUserAdmin)