# accounts/urls.py
from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    RegisterView,
    ProfileView,
    ProfileUpdateView,
    PasswordChangeView,
    DashboardView,
)

urlpatterns = [
    # Authentication URLs
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),

    # Profile URLs
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/change-password/', PasswordChangeView.as_view(), name='password_change'),

    # Dashboard URL
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]