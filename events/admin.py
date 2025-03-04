from django.contrib import admin

# Register your models here.
# admin.py
from django.contrib import admin
from .models import Club, ClubMembership, Event, EventRSVP

# Register your models here.

@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'founded_year')
    search_fields = ('name', 'description')
    list_filter = ('founded_year',)
    readonly_fields = ('social_media',)  # Make social_media read-only in admin


@admin.register(ClubMembership)
class ClubMembershipAdmin(admin.ModelAdmin):
    list_display = ('club', 'user', 'role', 'joined_date')
    search_fields = ('club__name', 'user__username', 'role')
    list_filter = ('club', 'role', 'joined_date')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_datetime', 'end_datetime', 'location', 'organizer', 'is_university_wide')
    search_fields = ('title', 'description', 'location', 'organizer__name')
    list_filter = ('start_datetime', 'is_university_wide', 'organizer')
    readonly_fields = ('tags',)  # Make tags read-only in admin


@admin.register(EventRSVP)
class EventRSVPAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'status', 'timestamp')
    search_fields = ('event__title', 'user__username', 'status')
    list_filter = ('event', 'status', 'timestamp')