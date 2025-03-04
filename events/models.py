from django.db import models

# Create your models here.
# models.py
from django.db import models


class Club(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    logo = models.ImageField(upload_to='club_logos/', blank=True, null=True)
    founded_year = models.PositiveIntegerField()
    social_media = models.JSONField(default=dict, blank=True)  # For storing social media links


class ClubMembership(models.Model):
    ROLES = (
        ('member', 'Member'),
        ('officer', 'Officer'),
        ('president', 'President'),
        ('advisor', 'Faculty Advisor'),
    )
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='club_memberships')
    role = models.CharField(max_length=20, choices=ROLES, default='member')
    joined_date = models.DateField(auto_now_add=True)


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    organizer = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='events', null=True, blank=True)
    is_university_wide = models.BooleanField(default=False)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)  # For event categorization and AI recommendations


class EventRSVP(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='event_rsvps')
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('going', 'Going'),
        ('maybe', 'Maybe'),
        ('not_going', 'Not Going')
    ])