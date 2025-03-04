# academics/urls.py
from django.urls import path

from . import views
from .views import (
    DepartmentListView,
    DepartmentDetailView,
    FacultyListView,
    FacultyDetailView,
    CourseListView,
    CourseDetailView,
    MyScheduleView,
    ClassSectionDetailView,
    EnrollView,
    DropClassView,
    AssignmentListView,
    ExamListView,
)

app_name = 'academics'  # Namespace for the app

urlpatterns = [
    # Department URLs
    path('departments/', DepartmentListView.as_view(), name='department_list'),
    path('departments/<int:pk>/', DepartmentDetailView.as_view(), name='department_detail'),

    # Faculty URLs
    path('faculty/', FacultyListView.as_view(), name='faculty_list'),
    path('faculty/<int:pk>/', FacultyDetailView.as_view(), name='faculty_detail'),

    # Course URLs
    path('courses/', CourseListView.as_view(), name='course_list'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course_detail'),

    # Class Section URLs
    path('sections/<int:pk>/', ClassSectionDetailView.as_view(), name='class_section_detail'),
    path('sections/<int:pk>/enroll/', EnrollView.as_view(), name='enroll'),
    path('sections/<int:pk>/drop/', DropClassView.as_view(), name='drop_class'),

    # My Schedule URL
    path('class-schedule/<int:pk>/', views.ClassScheduleView.as_view(), name='class_schedule'),
    path('my-schedule/', MyScheduleView.as_view(), name='my_schedule'),
    path('my-schedule/<int:section_id>/', MyScheduleView.as_view(), name='my_schedule_section'),

    # Assignment URLs
    path('assignments/', AssignmentListView.as_view(), name='assignment_list'),

    # Exam URLs
    path('exams/', ExamListView.as_view(), name='exam_list'),
]