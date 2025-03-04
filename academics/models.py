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
    office_phone = models.CharField(max_length=50, blank=True, null=True)
    research_interests = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='faculty_profiles/', null=True, blank=True)
    # Rename this field to avoid conflict
    office_hours_text = models.TextField(blank=True)

class OfficeHour(models.Model):
    DAYS = (
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    )
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='office_hours')
    day = models.CharField(max_length=3, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day']

class Education(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='education')
    degree = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    year = models.PositiveIntegerField()
    field_of_study = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-year']
        verbose_name_plural = 'Education'

class Publication(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='publications')
    title = models.CharField(max_length=500)
    journal = models.CharField(max_length=200)
    year = models.PositiveIntegerField()
    citation = models.TextField()
    url = models.URLField(blank=True, null=True)
    doi = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-year', 'title']

class Course(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    description = models.TextField()
    credit_hours = models.DecimalField(max_digits=3, decimal_places=1)
    default_schedule = models.TextField(blank=True, help_text="JSON format of default schedule pattern")

    def __str__(self):
        return f"{self.code}: {self.name}"


class ClassSection(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    section_number = models.CharField(max_length=10)
    semester = models.CharField(max_length=20)  # Fall 2023, Spring 2024, etc.
    instructor = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='classes')
    location = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    enrolled = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.course.code} {self.section_number} ({self.semester})"

    def assign_instructor(self, faculty):
        """Assign a faculty member as the instructor for this class section"""
        if faculty.department == self.course.department:
            self.instructor = faculty
            self.save()
            return True
        return False

    def create_schedule_from_pattern(self, schedule_pattern=None):
        """
        Create class schedules based on a pattern or course default
        Example pattern: [{'day': 'MON', 'start': '09:00', 'end': '10:30'},
                          {'day': 'WED', 'start': '09:00', 'end': '10:30'}]
        """
        from json import loads

        # Use provided pattern or fall back to course default
        if not schedule_pattern and self.course.default_schedule:
            try:
                schedule_pattern = loads(self.course.default_schedule)
            except:
                return []

        if not schedule_pattern:
            return []

        schedules = []
        for entry in schedule_pattern:
            schedule = ClassSchedule.objects.create(
                class_section=self,
                day=entry.get('day'),
                start_time=entry.get('start'),
                end_time=entry.get('end')
            )
            schedules.append(schedule)
        return schedules


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


class CourseAssignment(models.Model):
    """Tracks which faculty members can teach which courses"""
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='course_qualifications')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='qualified_faculty')
    is_primary = models.BooleanField(default=False, help_text="Primary instructor for this course")
    date_qualified = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ['faculty', 'course']

    def __str__(self):
        return f"{self.faculty.user.get_full_name()} - {self.course.code}"
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


class StudentSchedule(models.Model):
    student = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='student_schedules')
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE, related_name='student_schedules')
    semester = models.CharField(max_length=20)  # Fall 2023, Spring 2024, etc.

    # Cached data from ClassSchedule for quicker access
    day = models.CharField(max_length=3, choices=ClassSchedule.DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=100)

    # Additional fields for student-specific schedule information
    attendance_count = models.PositiveIntegerField(default=0)
    last_attended = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ['student', 'class_section', 'day']
        ordering = ['day', 'start_time']

    def save(self, *args, **kwargs):
        # Auto-populate semester from class section if not provided
        if not self.semester and self.class_section:
            self.semester = self.class_section.semester

        # Auto-populate location from class section if not provided
        if not self.location and self.class_section:
            self.location = self.class_section.location

        super().save(*args, **kwargs)

    @classmethod
    def create_from_enrollment(cls, enrollment):
        """Create schedule entries for a student from their enrollment"""
        schedules = []
        for class_schedule in enrollment.class_section.schedules.all():
            schedule, created = cls.objects.get_or_create(
                student=enrollment.student,
                class_section=enrollment.class_section,
                day=class_schedule.day,
                defaults={
                    'start_time': class_schedule.start_time,
                    'end_time': class_schedule.end_time,
                    'semester': enrollment.class_section.semester,
                    'location': enrollment.class_section.location,
                }
            )
            schedules.append(schedule)
        return schedules
# Add this to the Faculty model in academics/models.py
def is_department_head(self):
    """Check if this faculty member is the head of their department"""
    # This is a simple implementation - you might want to add a field in the Department model
    # to explicitly store this relationship
    return Department.objects.filter(
        id=self.department.id,
        faculty=self
    ).exists() and self.title in ['Department Head', 'Chair', 'Department Chair']