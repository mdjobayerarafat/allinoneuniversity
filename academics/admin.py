# admin.py
from django.contrib import admin
from .models import (
    Department,
    Faculty,
    Course,
    ClassSection,
    ClassSchedule,
    Enrollment,
    Assignment,
    Exam,
)

# Register your models here.

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    list_filter = ('name',)


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'title', 'office_location')
    search_fields = ('user__username', 'department__name', 'title')
    list_filter = ('department', 'title')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'credit_hours')
    search_fields = ('code', 'name', 'department__name')
    list_filter = ('department',)


@admin.register(ClassSection)
class ClassSectionAdmin(admin.ModelAdmin):
    list_display = ('course', 'section_number', 'semester', 'instructor', 'location', 'capacity', 'enrolled')
    search_fields = ('course__name', 'section_number', 'instructor__user__username')
    list_filter = ('course__department', 'semester', 'instructor')


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ('class_section', 'day', 'start_time', 'end_time')
    search_fields = ('class_section__course__name', 'day')
    list_filter = ('day', 'class_section__course__department')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_section', 'date_enrolled')
    search_fields = ('student__username', 'class_section__course__name')
    list_filter = ('class_section__course__department', 'date_enrolled')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('class_section', 'title', 'due_date', 'points_possible')
    search_fields = ('class_section__course__name', 'title')
    list_filter = ('class_section__course__department', 'due_date')


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('class_section', 'title', 'date', 'location', 'duration_minutes')
    search_fields = ('class_section__course__name', 'title', 'location')
    list_filter = ('class_section__course__department', 'date')