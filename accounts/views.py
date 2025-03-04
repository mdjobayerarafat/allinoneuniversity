import logging
import os

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, UpdateView, DetailView, FormView
from django.urls import reverse_lazy
from django.contrib import messages

from .models import User
from .forms import UserLoginForm, UserRegistrationForm, UserProfileForm, PasswordChangeForm

# Create logger
logger = logging.getLogger(__name__)


class LoginView(FormView):
    template_name = 'accounts/login.html'
    form_class = UserLoginForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')

        logger.info(f"Attempting login for username: {username}")

        # Debug authentication details
        try:
            user_obj = User.objects.get(username=username)
            logger.info(f"User found in database: {username}")
            logger.info(f"User is_active: {user_obj.is_active}")
            logger.info(f"Password check: {user_obj.check_password(password)}")
        except User.DoesNotExist:
            logger.warning(f"User {username} not found in database")

        # Use authenticate with request
        user = authenticate(self.request, username=username, password=password)
        logger.info(f"Authentication result: {'Success' if user else 'Failed'}")

        if user is not None:
            if user.is_active:
                login(self.request, user)
                logger.info(f"Login successful for {username}")
                messages.success(self.request, f'Welcome back, {user.first_name}!')

                next_url = self.request.GET.get('next')
                if next_url:
                    return redirect(next_url)

                return redirect(self.get_success_url())
            else:
                messages.error(self.request, 'Your account is inactive.')
                return self.form_invalid(form)
        else:
            messages.error(self.request, 'Invalid username or password.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.warning(f"Form validation failed: {form.errors}")
        return super().form_invalid(form)


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('login')


class RegisterView(FormView):
    template_name = 'accounts/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        # Let the form's save method handle password hashing
        user = form.save()
        # Don't call user.set_password again (form.save already does this)
        messages.success(self.request, 'Account created successfully! You can now log in.')
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'
    login_url = '/accounts/login/'

    def get_object(self):
        return self.request.user














class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('profile')
    login_url = '/accounts/login/'

    def get_object(self):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # This adds request.FILES to the form
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'files': self.request.FILES
            })
        return kwargs

    def form_valid(self, form):
        # Check if a new profile picture was uploaded
        if 'profile_picture' in self.request.FILES:
            # Delete old profile picture if it exists
            old_picture = self.request.user.profile_picture
            if old_picture and os.path.isfile(old_picture.path):
                try:
                    os.remove(old_picture.path)
                except (FileNotFoundError, PermissionError) as e:
                    # Log the error but continue
                    logger.error(f"Failed to delete old profile picture: {e}")

        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


class PasswordChangeView(LoginRequiredMixin, FormView):
    template_name = 'accounts/password_change.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('profile')
    login_url = '/accounts/login/'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        user.set_password(form.cleaned_data.get('new_password'))
        user.save()
        messages.success(self.request, 'Password changed successfully!')
        login(self.request, user)  # Keep user logged in
        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'
    redirect_field_name = 'next'

    def get(self, request):
        # Debug logging to check user authentication status
        logger.info(f"Dashboard accessed by: {request.user.username}")
        logger.info(f"User authenticated: {request.user.is_authenticated}")
        logger.info(f"User role: {request.user.role if hasattr(request.user, 'role') else 'No role'}")
        logger.info(f"User is_active: {request.user.is_active}")

        # Get user-specific data for the dashboard
        context = {
            'user': request.user,
            # Add more context data for different user roles if needed
        }

        # Render the dashboard with user context
        return render(request, 'accounts/dashboard.html', context)


def debug_auth(request):
    """Temporary debug view to troubleshoot authentication issues"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if user exists
        try:
            user = User.objects.get(username=username)

            # Test direct password validation
            password_valid = user.check_password(password)

            # Test authenticate method
            auth_user = authenticate(request, username=username, password=password)

            context = {
                'user_exists': True,
                'password_valid': password_valid,
                'auth_successful': auth_user is not None,
                'is_active': user.is_active
            }
        except User.DoesNotExist:
            context = {'user_exists': False}

        return render(request, 'accounts/debug_auth.html', context)

    return render(request, 'accounts/debug_auth.html')