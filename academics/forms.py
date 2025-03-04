from django import forms
from django.contrib.auth import get_user_model
from .models import Department, Faculty, Course, ClassSection, Assignment, Exam, ClassSchedule

User = get_user_model()


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class FacultyForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()

    class Meta:
        model = Faculty
        fields = ['first_name', 'last_name', 'email', 'department', 'title',
                  'office_location', 'office_hours', 'research_interests']
        widgets = {
            'office_hours': forms.Textarea(attrs={'rows': 3}),
            'research_interests': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance:
            initial = kwargs.get('initial', {})
            initial['first_name'] = instance.user.first_name
            initial['last_name'] = instance.user.last_name
            initial['email'] = instance.user.email
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'name', 'department', 'description', 'credit_hours']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ClassSectionForm(forms.ModelForm):
    class Meta:
        model = ClassSection
        fields = ['course', 'section_number', 'semester', 'instructor',
                  'location', 'capacity']

        SEMESTER_CHOICES = [
            ('Spring 2025', 'Spring 2025'),
            ('Summer 2025', 'Summer 2025'),
            ('Fall 2025', 'Fall 2025'),
            ('Spring 2026', 'Spring 2026'),
        ]

        widgets = {
            'semester': forms.Select(choices=SEMESTER_CHOICES),
        }


class ClassScheduleForm(forms.ModelForm):
    class Meta:
        model = ClassSchedule
        fields = ['day', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class ClassScheduleFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        # Validate that there are no time conflicts for the same day
        schedules = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                day = form.cleaned_data.get('day')
                start_time = form.cleaned_data.get('start_time')
                end_time = form.cleaned_data.get('end_time')

                if not all([day, start_time, end_time]):
                    continue

                if end_time <= start_time:
                    form.add_error('end_time', 'End time must be after start time')

                # Check for overlaps with other schedules on the same day
                for existing_day, existing_start, existing_end in schedules:
                    if day == existing_day:
                        if (start_time <= existing_end and end_time >= existing_start):
                            form.add_error('start_time', 'This time overlaps with another schedule on the same day')
                            break

                schedules.append((day, start_time, end_time))


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['class_section', 'title', 'description', 'due_date', 'points_possible']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['class_section', 'title', 'date', 'location', 'duration_minutes']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class EnrollmentFilterForm(forms.Form):
    semester = forms.ChoiceField(
        choices=[
            ('', 'All Semesters'),
            ('Spring 2025', 'Spring 2025'),
            ('Summer 2025', 'Summer 2025'),
            ('Fall 2025', 'Fall 2025'),
        ],
        required=False
    )


class CourseSearchForm(forms.Form):
    search = forms.CharField(required=False, label='Search',
                             widget=forms.TextInput(attrs={'placeholder': 'Search by name or code'}))
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label='All Departments'
    )


class FacultySearchForm(forms.Form):
    search = forms.CharField(required=False, label='Search',
                             widget=forms.TextInput(attrs={'placeholder': 'Search by name or title'}))
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label='All Departments'
    )


class AssignmentFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Assignments'),
        ('upcoming', 'Upcoming'),
        ('past', 'Past'),
    ]

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    class_section = forms.ModelChoiceField(
        queryset=None,  # This will be set in __init__
        required=False,
        empty_label='All Classes'
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['class_section'].queryset = ClassSection.objects.filter(
                enrollments__student=user
            ).select_related('course')


class ExamFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Exams'),
        ('upcoming', 'Upcoming'),
        ('past', 'Past'),
    ]

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    class_section = forms.ModelChoiceField(
        queryset=None,  # This will be set in __init__
        required=False,
        empty_label='All Classes'
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['class_section'].queryset = ClassSection.objects.filter(
                enrollments__student=user
            ).select_related('course')
