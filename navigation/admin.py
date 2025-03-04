# admin.py
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.contrib.gis.forms import OSMWidget  # For custom map widget
from .models import Building, Room, ARMarker

# Register your models here.

@admin.register(Building)
class BuildingAdmin(GISModelAdmin):
    list_display = ('name', 'code', 'floors', 'description')
    search_fields = ('name', 'code', 'description')
    list_filter = ('floors',)
    readonly_fields = ('formatted_hours_of_operation',)  # Custom method for display

    def formatted_hours_of_operation(self, obj):
        return str(obj.hours_of_operation)  # Convert JSON to string for display
    formatted_hours_of_operation.short_description = 'Hours of Operation'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('building', 'number', 'floor', 'room_type', 'capacity')
    search_fields = ('building__name', 'number', 'room_type')
    list_filter = ('building', 'floor', 'room_type')


@admin.register(ARMarker)
class ARMarkerAdmin(GISModelAdmin):
    list_display = ('name', 'building', 'marker_type', 'content')
    search_fields = ('name', 'building__name', 'marker_type', 'content')
    list_filter = ('building', 'marker_type')

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'location':
            kwargs['widget'] = OSMWidget  # Use OpenStreetMap widget
        return super().formfield_for_dbfield(db_field, **kwargs)