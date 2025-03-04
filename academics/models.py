from django.db import models

# Create your models here.
# models.py
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    description = models.TextField(blank=True)


class Faculty(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='faculty')
    title = models.CharField(max_length=50)  # Professor, Associate Professor, etc.
    office_location = models.CharField(max_length=100)
    office_hours = models.TextField()
    research_interests = models.TextField(blank=True)


class Course(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    description = models.TextField()
    credit_hours = models.DecimalField(max_digits=3, decimal_places=1)


class ClassSection(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    section_number = models.CharField(max_length=10)
    semester = models.CharField(max_length=20)  # Fall 2023, Spring 2024, etc.
    instructor = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='classes')
    location = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    enrolled = models.PositiveIntegerField(default=0)


class ClassSchedule(models.Model):
    DAYS = (
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    )
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name='schedules')
    day = models.CharField(max_length=3, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()


class Enrollment(models.Model):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='enrollments')
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name='enrollments')
    date_enrolled = models.DateField(auto_now_add=True)


class Assignment(models.Model):
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    points_possible = models.PositiveIntegerField()


class Exam(models.Model):
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name='exams')
    title = models.CharField(max_length=200)
    date = models.DateTimeField()
    location = models.CharField(max_length=100)
    duration_minutes = models.PositiveIntegerField()