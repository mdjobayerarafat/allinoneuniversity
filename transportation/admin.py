# admin.py
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

# For GIS fields
from .models import BusRoute, BusStop, RouteStop, BusSchedule, Bus, BusAlert

# Register your models here.

@admin.register(BusRoute)
class BusRouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'color_code', 'active')
    search_fields = ('name', 'description')
    list_filter = ('active',)


@admin.register(BusStop)
class BusStopAdmin(GISModelAdmin):  # Inherit from OSMGeoAdmin
    list_display = ('name', 'address', 'location')
    search_fields = ('name', 'address')
    list_filter = ('routes',)


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ('route', 'stop', 'order')
    search_fields = ('route__name', 'stop__name')
    list_filter = ('route', 'stop')


@admin.register(BusSchedule)
class BusScheduleAdmin(admin.ModelAdmin):
    list_display = ('route', 'day_of_week', 'start_time', 'end_time', 'frequency_minutes')
    search_fields = ('route__name', 'day_of_week')
    list_filter = ('route', 'day_of_week')


@admin.register(Bus)
class BusAdmin(GISModelAdmin):  # Inherit from OSMGeoAdmin
    list_display = ('bus_number', 'route', 'capacity', 'current_location', 'last_updated', 'is_active')
    search_fields = ('bus_number', 'route__name')
    list_filter = ('route', 'is_active')


@admin.register(BusAlert)
class BusAlertAdmin(admin.ModelAdmin):
    list_display = ('route', 'title', 'start_date', 'end_date', 'active')
    search_fields = ('route__name', 'title', 'description')
    list_filter = ('route', 'active', 'start_date', 'end_date')