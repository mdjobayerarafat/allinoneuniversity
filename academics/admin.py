from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Department, Faculty, OfficeHour, Course,
    ClassSection, ClassSchedule, Enrollment,
    Assignment, Exam, Education, Publication,
    StudentSchedule, CourseAssignment
)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

class OfficeHourInline(admin.TabularInline):
    model = OfficeHour
    extra = 1

class EducationInline(admin.TabularInline):
    model = Education
    extra = 0

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'title', 'department', 'course_count', 'is_head')
    list_filter = ('department', 'title')
    search_fields = ('user__first_name', 'user__last_name', 'title')
    inlines = [OfficeHourInline, EducationInline]

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'

    def course_count(self, obj):
        count = obj.course_qualifications.count()
        return format_html('<a href="/admin/academics/courseassignment/?faculty__id__exact={}">{}</a>',
                          obj.id, count)
    course_count.short_description = 'Assigned Courses'

    def is_head(self, obj):
        return obj.is_department_head()
    is_head.boolean = True
    is_head.short_description = 'Department Head'

class CourseAssignmentInline(admin.TabularInline):
    model = CourseAssignment
    extra = 1
    autocomplete_fields = ['faculty']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'credit_hours', 'qualified_faculty_count')
    list_filter = ('department', 'credit_hours')
    search_fields = ('code', 'name', 'description')
    inlines = [CourseAssignmentInline]

    def qualified_faculty_count(self, obj):
        count = obj.qualified_faculty.count()
        return format_html('<a href="/admin/academics/courseassignment/?course__id__exact={}">{}</a>',
                          obj.id, count)
    qualified_faculty_count.short_description = 'Faculty'

class ClassScheduleInline(admin.TabularInline):
    model = ClassSchedule
    extra = 1

@admin.register(ClassSection)
class ClassSectionAdmin(admin.ModelAdmin):
    list_display = ['course', 'section_number', 'semester', 'instructor', 'capacity', 'enrolled', 'schedule_count']
    list_filter = ['semester', 'course__department', 'instructor']
    search_fields = ['course__code', 'course__name', 'instructor__user__last_name', 'section_number']
    raw_id_fields = ['instructor']
    autocomplete_fields = ['course']
    inlines = [ClassScheduleInline]

    def schedule_count(self, obj):
        count = obj.schedules.count()
        return count
    schedule_count.short_description = 'Schedules'

    actions = ['add_default_schedule', 'assign_recommended_faculty']

    def add_default_schedule(self, request, queryset):
        schedule_count = 0
        for section in queryset:
            new_schedules = section.create_schedule_from_pattern()
            schedule_count += len(new_schedules)

        self.message_user(request, f"Created {schedule_count} schedule entries for {queryset.count()} section(s)")
    add_default_schedule.short_description = "Add default schedule from course pattern"

    def assign_recommended_faculty(self, request, queryset):
        assigned = 0
        for section in queryset:
            # Find primary qualified instructor for this course
            qualified = CourseAssignment.objects.filter(
                course=section.course,
                is_primary=True
            ).first()

            if qualified:
                section.instructor = qualified.faculty
                section.save()
                assigned += 1

        self.message_user(request, f"Assigned recommended faculty to {assigned} section(s)")
    assign_recommended_faculty.short_description = "Assign recommended faculty"

@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ['class_section', 'day', 'start_time', 'end_time']
    list_filter = ['day', 'class_section__course', 'class_section__semester']
    search_fields = ['class_section__course__code', 'class_section__section_number']
    autocomplete_fields = ['class_section']

@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ['faculty', 'course', 'is_primary', 'date_qualified']
    list_filter = ['is_primary', 'course__department', 'faculty__department']
    search_fields = ['faculty__user__first_name', 'faculty__user__last_name', 'course__code', 'course__name']
    autocomplete_fields = ['faculty', 'course']

    actions = ['mark_as_primary', 'mark_as_secondary']

    def mark_as_primary(self, request, queryset):
        queryset.update(is_primary=True)
        self.message_user(request, f"Marked {queryset.count()} assignments as primary")
    mark_as_primary.short_description = "Mark selected as primary instructors"

    def mark_as_secondary(self, request, queryset):
        queryset.update(is_primary=False)
        self.message_user(request, f"Marked {queryset.count()} assignments as secondary")
    mark_as_secondary.short_description = "Mark selected as secondary instructors"

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_section', 'date_enrolled')
    list_filter = ('class_section__semester',)
    search_fields = ('student__username', 'student__last_name', 'class_section__course__code')
    date_hierarchy = 'date_enrolled'
    actions = ['create_student_schedules']

    def create_student_schedules(self, request, queryset):
        schedule_count = 0
        for enrollment in queryset:
            schedules = StudentSchedule.create_from_enrollment(enrollment)
            schedule_count += len(schedules)

        self.message_user(request, f"Created {schedule_count} student schedule entries")
    create_student_schedules.short_description = "Create student schedules from enrollments"

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'class_section', 'due_date', 'points_possible')
    list_filter = ('class_section__semester', 'class_section__course')
    search_fields = ('title', 'class_section__course__code')
    date_hierarchy = 'due_date'

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'class_section', 'date', 'duration_minutes')
    list_filter = ('class_section__semester', 'class_section__course')
    search_fields = ('title', 'class_section__course__code')
    date_hierarchy = 'date'

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('faculty', 'degree', 'institution', 'year')
    list_filter = ('institution', 'year')
    search_fields = ('degree', 'institution', 'faculty__user__last_name')

@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('faculty', 'title', 'journal', 'year')
    list_filter = ('journal', 'year')
    search_fields = ('title', 'journal', 'faculty__user__last_name')

@admin.register(StudentSchedule)
class StudentScheduleAdmin(admin.ModelAdmin):
    list_display = ['student', 'class_section', 'day', 'start_time', 'end_time', 'location', 'attendance_count']
    list_filter = ['semester', 'day', 'class_section__course']
    search_fields = ['student__username', 'student__email', 'class_section__course__code', 'class_section__course__name']
    raw_id_fields = ['student', 'class_section']