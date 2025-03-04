from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Department, Faculty, Course, ClassSection, Enrollment, Assignment, Exam, ClassSchedule


class DepartmentListView(ListView):
    model = Department
    template_name = 'academics/departments.html'
    context_object_name = 'departments'


class DepartmentDetailView(DetailView):
    model = Department
    template_name = 'academics/department_detail.html'
    context_object_name = 'department'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        department = self.object
        context['faculty'] = Faculty.objects.filter(department=department)
        context['courses'] = Course.objects.filter(department=department)
        return context


class FacultyListView(ListView):
    model = Faculty
    template_name = 'academics/faculty_list.html'
    context_object_name = 'faculty'

    def get_queryset(self):
        queryset = Faculty.objects.all()
        department_id = self.request.GET.get('department')
        search = self.request.GET.get('search')

        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(title__icontains=search)
            )

        return queryset


class FacultyDetailView(DetailView):
    model = Faculty
    template_name = 'academics/faculty_detail.html'
    context_object_name = 'faculty_member'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty = self.object
        current_semester = "Spring 2025"  # This could be determined programmatically
        context['classes'] = ClassSection.objects.filter(instructor=faculty, semester=current_semester)
        return context


class CourseListView(ListView):
    model = Course
    template_name = 'academics/courses.html'
    context_object_name = 'courses'

    def get_queryset(self):
        queryset = Course.objects.all()
        department_id = self.request.GET.get('department')
        search = self.request.GET.get('search')

        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset


class CourseDetailView(DetailView):
    model = Course
    template_name = 'academics/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        current_semester = "Spring 2025"  # This could be determined programmatically
        context['sections'] = ClassSection.objects.filter(course=course, semester=current_semester)
        return context


class ClassScheduleView(LoginRequiredMixin, DetailView):
    model = ClassSection
    template_name = 'academics/class_schedule.html'
    context_object_name = 'section'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section = self.object

        # Get all schedules for this class section
        context['schedules'] = section.schedules.all().order_by('day')

        # Add day labels dictionary for easy rendering
        context['day_labels'] = dict(ClassSchedule.DAYS)

        # Add enrollment status if user is logged in
        if self.request.user.is_authenticated:
            context['is_enrolled'] = Enrollment.objects.filter(
                student=self.request.user,
                class_section=section
            ).exists()

        return context
class MyScheduleView(LoginRequiredMixin, View):
            template_name = 'academics/my_schedule.html'

            def get(self, request, section_id=None):
                # Get current semester enrollments
                current_semester = "Spring 2025"  # Could be determined programmatically
                enrollments = Enrollment.objects.filter(
                    student=self.request.user,
                    class_section__semester=current_semester
                ).select_related('class_section', 'class_section__course', 'class_section__instructor')

                # Check if user has any enrollments
                if not enrollments.exists():
                    context = {
                        'no_enrollments': True,
                        'day_labels': dict(ClassSchedule.DAYS)
                    }
                    messages.info(request, "You are not enrolled in any classes this semester.")
                    return render(request, self.template_name, context)

                # Get the section ID from the URL parameter or query param or use the first enrollment
                if section_id:
                    try:
                        # Verify user is enrolled in this section
                        section = ClassSection.objects.get(
                            id=section_id,
                            enrollments__student=request.user
                        )
                    except ClassSection.DoesNotExist:
                        # If not enrolled or doesn't exist, use first enrollment
                        section = enrollments.first().class_section
                else:
                    section_id_from_query = request.GET.get('section')
                    if section_id_from_query:
                        try:
                            section = ClassSection.objects.get(
                                id=section_id_from_query,
                                enrollments__student=request.user
                            )
                        except ClassSection.DoesNotExist:
                            section = enrollments.first().class_section
                    else:
                        # Default to first enrollment if no section specified
                        section = enrollments.first().class_section

                # Get all schedules for this specific section
                schedules = section.schedules.all().order_by('day')

                # Get upcoming assignments and exams for this section
                now = timezone.now()
                upcoming_assignments = Assignment.objects.filter(
                    class_section=section,
                    due_date__gte=now
                ).order_by('due_date')[:5]

                upcoming_exams = Exam.objects.filter(
                    class_section=section,
                    date__gte=now
                ).order_by('date')[:5]

                context = {
                    'section': section,
                    'schedules': schedules,
                    'day_labels': dict(ClassSchedule.DAYS),
                    'upcoming_assignments': upcoming_assignments,
                    'upcoming_exams': upcoming_exams,
                    'enrollments': enrollments,
                    'is_enrolled': True,
                    'no_enrollments': False
                }

                return render(request, self.template_name, context)

class ClassSectionDetailView(DetailView):
    model = ClassSection
    template_name = 'academics/class_section_detail.html'
    context_object_name = 'section'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section = self.object
        context['schedules'] = section.schedules.all()
        context['assignments'] = Assignment.objects.filter(class_section=section).order_by('due_date')
        context['exams'] = Exam.objects.filter(class_section=section).order_by('date')

        if self.request.user.is_authenticated:
            context['is_enrolled'] = Enrollment.objects.filter(
                student=self.request.user,
                class_section=section
            ).exists()

        return context


class EnrollView(LoginRequiredMixin, View):
    def post(self, request, pk):
        section = get_object_or_404(ClassSection, pk=pk)

        # Check if already enrolled
        if Enrollment.objects.filter(student=request.user, class_section=section).exists():
            messages.warning(request, "You are already enrolled in this class.")
            return redirect('academics:class_section_detail', pk=pk)

        # Check if class is full
        if section.enrolled >= section.capacity:
            messages.error(request, "This class is full.")
            return redirect('academics:class_section_detail', pk=pk)

        # Create enrollment
        Enrollment.objects.create(student=request.user, class_section=section)

        # Update enrolled count
        section.enrolled += 1
        section.save()

        messages.success(request, f"Successfully enrolled in {section.course.code} {section.section_number}.")
        return redirect('academics:my_schedule')


class DropClassView(LoginRequiredMixin, View):
    def post(self, request, pk):
        section = get_object_or_404(ClassSection, pk=pk)

        # Check if enrolled
        enrollment = Enrollment.objects.filter(student=request.user, class_section=section).first()
        if not enrollment:
            messages.warning(request, "You are not enrolled in this class.")
            return redirect('academics:class_section_detail', pk=pk)

        # Delete enrollment
        enrollment.delete()

        # Update enrolled count
        section.enrolled -= 1
        section.save()

        messages.success(request, f"Successfully dropped {section.course.code} {section.section_number}.")
        return redirect('academics:my_schedule')


class AssignmentListView(LoginRequiredMixin, ListView):
    template_name = 'academics/assignments.html'
    context_object_name = 'assignments'

    def get_queryset(self):
        # Get all class sections the student is enrolled in
        enrollments = Enrollment.objects.filter(student=self.request.user)
        section_ids = [e.class_section_id for e in enrollments]

        # Get assignments for those sections
        queryset = Assignment.objects.filter(class_section_id__in=section_ids)

        # Filter by status if provided
        status = self.request.GET.get('status')
        if status == 'upcoming':
            queryset = queryset.filter(due_date__gte=timezone.now())
        elif status == 'past':
            queryset = queryset.filter(due_date__lt=timezone.now())

        return queryset.order_by('due_date')


class ExamListView(LoginRequiredMixin, ListView):
    template_name = 'academics/exams.html'
    context_object_name = 'exams'

    def get_queryset(self):
        # Get all class sections the student is enrolled in
        enrollments = Enrollment.objects.filter(student=self.request.user)
        section_ids = [e.class_section_id for e in enrollments]

        # Get exams for those sections
        queryset = Exam.objects.filter(class_section_id__in=section_ids)

        # Filter by status if provided
        status = self.request.GET.get('status')
        if status == 'upcoming':
            queryset = queryset.filter(date__gte=timezone.now())
        elif status == 'past':
            queryset = queryset.filter(date__lt=timezone.now())

        return queryset.order_by('date')

class FacultyDashboardView(LoginRequiredMixin, View):
    template_name = 'academics/faculty/dashboard.html'

    def get(self, request):
        try:
            faculty = Faculty.objects.get(user=request.user)
            is_department_head = faculty.is_department_head()
            current_semester = "Spring 2025"  # Could be determined programmatically

            # Get classes taught by this faculty
            classes = ClassSection.objects.filter(
                instructor=faculty,
                semester=current_semester
            ).select_related('course')

            # Get qualified courses
            qualified_courses = Course.objects.filter(
                qualified_faculty__faculty=faculty
            ).distinct()

            # Get department data if department head
            department_data = None
            if is_department_head:
                department_faculty = Faculty.objects.filter(department=faculty.department)
                department_courses = Course.objects.filter(department=faculty.department)
                department_sections = ClassSection.objects.filter(
                    course__department=faculty.department,
                    semester=current_semester
                )
                department_data = {
                    'faculty_count': department_faculty.count(),
                    'course_count': department_courses.count(),
                    'section_count': department_sections.count()
                }

            context = {
                'faculty': faculty,
                'is_department_head': is_department_head,
                'classes': classes,
                'qualified_courses': qualified_courses,
                'department_data': department_data
            }
            return render(request, self.template_name, context)
        except Faculty.DoesNotExist:
            messages.error(request, "You don't have faculty privileges.")
            return redirect('home')

class FacultyClassListView(LoginRequiredMixin, ListView):
    template_name = 'academics/faculty/class_list.html'
    context_object_name = 'classes'

    def get_queryset(self):
        try:
            faculty = Faculty.objects.get(user=self.request.user)
            semester = self.request.GET.get('semester', "Spring 2025")

            # Department heads can see all department classes
            if faculty.is_department_head():
                return ClassSection.objects.filter(
                    course__department=faculty.department,
                    semester=semester
                ).select_related('course', 'instructor')

            # Regular faculty see only their classes
            return ClassSection.objects.filter(
                instructor=faculty,
                semester=semester
            ).select_related('course')
        except Faculty.DoesNotExist:
            return ClassSection.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            faculty = Faculty.objects.get(user=self.request.user)
            context['faculty'] = faculty
            context['is_department_head'] = faculty.is_department_head()
            context['current_semester'] = self.request.GET.get('semester', "Spring 2025")
        except Faculty.DoesNotExist:
            context['is_department_head'] = False
        return context

class FacultyClassDetailView(LoginRequiredMixin, DetailView):
    model = ClassSection
    template_name = 'academics/faculty/class_detail.html'
    context_object_name = 'section'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty = Faculty.objects.get(user=self.request.user)
        section = self.object

        # Check if user is authorized to view this section
        if section.instructor == faculty or (faculty.is_department_head() and section.course.department == faculty.department):
            context['is_authorized'] = True
            context['is_instructor'] = section.instructor == faculty
            context['is_department_head'] = faculty.is_department_head()
            context['schedules'] = section.schedules.all().order_by('day')
            context['enrolled_students'] = section.enrollments.select_related('student').order_by('student__last_name')
            context['assignments'] = section.assignments.all().order_by('due_date')
            context['exams'] = section.exams.all().order_by('date')
        else:
            context['is_authorized'] = False

        return context

class FacultyClassScheduleEditView(LoginRequiredMixin, View):
    template_name = 'academics/faculty/schedule_edit.html'

    def get(self, request, pk):
        section = get_object_or_404(ClassSection, pk=pk)
        faculty = get_object_or_404(Faculty, user=request.user)

        # Check authorization
        if not (section.instructor == faculty or (faculty.is_department_head() and section.course.department == faculty.department)):
            messages.error(request, "You are not authorized to edit this schedule.")
            return redirect('academics:faculty_dashboard')

        schedules = section.schedules.all().order_by('day')
        context = {
            'section': section,
            'schedules': schedules,
            'day_choices': ClassSchedule.DAYS,
            'is_department_head': faculty.is_department_head(),
            'faculty': faculty
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        section = get_object_or_404(ClassSection, pk=pk)
        faculty = get_object_or_404(Faculty, user=request.user)

        # Check authorization
        if not (section.instructor == faculty or (faculty.is_department_head() and section.course.department == faculty.department)):
            messages.error(request, "You are not authorized to edit this schedule.")
            return redirect('academics:faculty_dashboard')

        # Delete existing schedules if replacing them
        if request.POST.get('replace_schedules'):
            section.schedules.all().delete()

        # Process new schedule entries
        days = request.POST.getlist('day')
        start_times = request.POST.getlist('start_time')
        end_times = request.POST.getlist('end_time')

        for i in range(len(days)):
            if i < len(start_times) and i < len(end_times):
                ClassSchedule.objects.create(
                    class_section=section,
                    day=days[i],
                    start_time=start_times[i],
                    end_time=end_times[i]
                )

        messages.success(request, f"Schedule for {section} has been updated.")
        return redirect('academics:faculty_class_detail', pk=section.pk)

class DepartmentHeadFacultyListView(LoginRequiredMixin, ListView):
    template_name = 'academics/faculty/department_faculty.html'
    context_object_name = 'faculty_members'

    def get_queryset(self):
        try:
            faculty = Faculty.objects.get(user=self.request.user)
            if faculty.is_department_head():
                return Faculty.objects.filter(department=faculty.department)
            return Faculty.objects.none()
        except Faculty.DoesNotExist:
            return Faculty.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            faculty = Faculty.objects.get(user=self.request.user)
            context['faculty'] = faculty
            context['is_department_head'] = faculty.is_department_head()
            context['department'] = faculty.department
        except Faculty.DoesNotExist:
            context['is_department_head'] = False
        return context

class DepartmentHeadCourseListView(LoginRequiredMixin, ListView):
    template_name = 'academics/faculty/department_courses.html'
    context_object_name = 'courses'

    def get_queryset(self):
        try:
            faculty = Faculty.objects.get(user=self.request.user)
            if faculty.is_department_head():
                return Course.objects.filter(department=faculty.department)
            return Course.objects.none()
        except Faculty.DoesNotExist:
            return Course.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            faculty = Faculty.objects.get(user=self.request.user)
            context['faculty'] = faculty
            context['is_department_head'] = faculty.is_department_head()
            context['department'] = faculty.department
        except Faculty.DoesNotExist:
            context['is_department_head'] = False
        return context


