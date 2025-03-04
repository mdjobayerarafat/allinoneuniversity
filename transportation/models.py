from django.db import models

# Create your models here.
# models.py
from django.db import models
from django.contrib.gis.db import models as gis_models  # For geographical features


class BusRoute(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color_code = models.CharField(max_length=7)  # Hex color code for the route
    active = models.BooleanField(default=True)


class BusStop(models.Model):
    name = models.CharField(max_length=100)
    location = gis_models.PointField()  # Geographical point
    address = models.CharField(max_length=200)
    routes = models.ManyToManyField(BusRoute, through='RouteStop', related_name='stops')


class RouteStop(models.Model):
    route = models.ForeignKey(BusRoute, on_delete=models.CASCADE)
    stop = models.ForeignKey(BusStop, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()  # The order of the stop in the route


class BusSchedule(models.Model):
    route = models.ForeignKey(BusRoute, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=10)  # Monday, Tuesday, etc.
    start_time = models.TimeField()
    end_time = models.TimeField()
    frequency_minutes = models.PositiveIntegerField()  # How often the bus comes


class Bus(models.Model):
    route = models.ForeignKey(BusRoute, on_delete=models.CASCADE, related_name='buses')
    bus_number = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField()
    current_location = gis_models.PointField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)


class BusAlert(models.Model):
    route = models.ForeignKey(BusRoute, on_delete=models.CASCADE, related_name='alerts')
    title = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    active = models.BooleanField(default=True)