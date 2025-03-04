from venv import logger

from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User



class UserLoginForm(forms.Form):
            username = forms.CharField(
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Username',
                    'id': 'id_username',
                    'autocomplete': 'username'
                })
            )
            password = forms.CharField(
                widget=forms.PasswordInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Password',
                    'id': 'id_password',
                    'autocomplete': 'current-password'
                })
            )

            def __init__(self, *args, **kwargs):
                self.request = kwargs.pop('request', None)
                super().__init__(*args, **kwargs)

            def clean(self):
                cleaned_data = super().clean()
                username = cleaned_data.get('username', '').strip()
                password = cleaned_data.get('password', '')

                if username and password:
                    # Debug logging
                    logger.info(f"Attempting login validation for username: {username}")

                    try:
                        user = User.objects.get(username__iexact=username)
                        logger.info(f"Found user in database: {user.username}")
                        logger.info(f"User is_active status: {user.is_active}")

                        if not user.is_active:
                            logger.warning(f"User {username} is inactive")
                            raise forms.ValidationError("This account is inactive.")

                        # Try authentication with correct case username
                        user_auth = authenticate(self.request, username=user.username, password=password)
                        logger.info(f"Authentication result for {username}: {user_auth is not None}")

                        if user_auth is None:
                            logger.warning(f"Authentication failed for user: {username}")
                            raise forms.ValidationError("Invalid username or password.")

                        cleaned_data['user'] = user_auth

                    except User.DoesNotExist:
                        logger.warning(f"User not found: {username}")
                        raise forms.ValidationError("Invalid username or password.")

                return cleaned_data
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'student_id', 'department']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student ID (if applicable)'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords don't match.")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student_id'].required = False
        self.fields['department'].required = False

        # Make student_id required only for student role
        if 'role' in self.data and self.data['role'] == 'student':
            self.fields['student_id'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hash the password
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'department', 'profile_picture', 'preferences']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'preferences': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preferences'].help_text = 'Enter preferences as JSON: {"theme": "dark", "notifications": true}'
        self.fields['department'].required = False
        self.fields['profile_picture'].required = False


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Current Password'})
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if self.user and not self.user.check_password(current_password):
            raise ValidationError("Incorrect current password.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "New passwords don't match.")

        return cleaned_data


class UserSearchForm(forms.Form):
    ROLE_CHOICES = [('', 'All Roles')] + list(User.ROLES)

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by name or username'})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    department = forms.ModelChoiceField(
        queryset=None,  # This will be set in __init__
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import here to avoid circular imports
        from academics.models import Department
        self.fields['department'].queryset = Department.objects.all()


class UserAdminForm(forms.ModelForm):
    """Form for administrators to edit user details"""

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'student_id', 'department', 'is_active',
            'is_staff', 'is_superuser'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student_id'].required = False
        self.fields['department'].required = False

        # Make fields required based on role
        if self.instance.role == 'student':
            self.fields['student_id'].required = True