# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLES = (
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),
        ('admin', 'Administrator'),
    )
    # Add default='student' to ensure all users have a role
    role = models.CharField(max_length=20, choices=ROLES, default='student')
    student_id = models.CharField(max_length=20, blank=True, null=True)
    department = models.ForeignKey('academics.Department', on_delete=models.SET_NULL, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    preferences = models.JSONField(default=dict, blank=True)  # For storing user preferences

    class Meta:
        db_table = 'accounts_user'  # Changed from 'auth_user' to a unique name

    # Add related_name attributes to solve the reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )