from django.db import models
from django.contrib.gis.db import models as gis_models


class Building(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    location = gis_models.PointField()
    floors = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='buildings/', blank=True, null=True)
    hours_of_operation = models.JSONField(default=dict, blank=True)


class Room(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='rooms')
    number = models.CharField(max_length=20)
    floor = models.PositiveIntegerField()
    room_type = models.CharField(max_length=50)  # Classroom, Office, Lab, etc.
    capacity = models.PositiveIntegerField(null=True, blank=True)


class ARMarker(models.Model):
    name = models.CharField(max_length=100)
    location = gis_models.PointField()
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='markers', null=True, blank=True)
    marker_type = models.CharField(max_length=50)  # QR code, image marker, etc.
    content = models.TextField()  # Information to display when the marker is scanned
    image = models.ImageField(upload_to='ar_markers/', blank=True, null=True)