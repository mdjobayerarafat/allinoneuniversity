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

from .models import Department, Faculty, Course, ClassSection, Enrollment, Assignment, Exam


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


class MyScheduleView(LoginRequiredMixin, ListView):
    template_name = 'academics/my_schedule.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        current_semester = "Spring 2025"  # This could be determined programmatically
        return Enrollment.objects.filter(
            student=self.request.user,
            class_section__semester=current_semester
        ).select_related('class_section', 'class_section__course', 'class_section__instructor')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Organize the schedule by day
        schedule = {
            'MON': [], 'TUE': [], 'WED': [], 'THU': [], 'FRI': [], 'SAT': [], 'SUN': []
        }

        for enrollment in context['enrollments']:
            class_schedules = enrollment.class_section.schedules.all()
            for class_schedule in class_schedules:
                schedule[class_schedule.day].append({
                    'section': enrollment.class_section,
                    'start_time': class_schedule.start_time,
                    'end_time': class_schedule.end_time
                })

        # Sort each day's classes by start time
        for day in schedule:
            schedule[day].sort(key=lambda x: x['start_time'])

        context['schedule'] = schedule

        # Get upcoming assignments and exams
        now = timezone.now()
        enrollments = context['enrollments']
        section_ids = [e.class_section_id for e in enrollments]

        context['upcoming_assignments'] = Assignment.objects.filter(
            class_section_id__in=section_ids,
            due_date__gte=now
        ).order_by('due_date')[:5]

        context['upcoming_exams'] = Exam.objects.filter(
            class_section_id__in=section_ids,
            date__gte=now
        ).order_by('date')[:5]

        return context


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


