from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import BusRoute, BusStop, Bus, BusAlert, BusSchedule

class BusRouteListView(ListView):
    model = BusRoute
    template_name = 'transportation/routes.html'
    context_object_name = 'routes'

    def get_queryset(self):
        queryset = BusRoute.objects.filter(active=True)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


class BusRouteDetailView(DetailView):
    model = BusRoute
    template_name = 'transportation/route_detail.html'
    context_object_name = 'route'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        route = self.object
        context['stops'] = BusStop.objects.filter(routes=route).order_by('routestop__order')

        today = timezone.now().strftime('%A')
        context['schedules'] = BusSchedule.objects.filter(route=route, day_of_week=today)

        context['active_buses'] = Bus.objects.filter(route=route, is_active=True)
        context['alerts'] = BusAlert.objects.filter(
            route=route,
            active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )

        return context


class BusStopDetailView(DetailView):
    model = BusStop
    template_name = 'transportation/stop_detail.html'
    context_object_name = 'stop'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stop = self.object
        context['routes'] = BusRoute.objects.filter(stops=stop, active=True)

        # Find the next arriving buses
        context['arriving_buses'] = []
        for route in context['routes']:
            active_buses = Bus.objects.filter(route=route, is_active=True)
            for bus in active_buses:
                # In a real app, you would calculate arrival time based on GPS position
                # This is just a placeholder
                arrival_time = timezone.now() + timezone.timedelta(minutes=5)
                context['arriving_buses'].append({
                    'route': route,
                    'bus': bus,
                    'arrival_time': arrival_time
                })

        return context


class BusTrackerView(View):
    def get(self, request):
        routes = BusRoute.objects.filter(active=True)
        return render(request, 'transportation/bus_tracker.html', {'routes': routes})


class BusAlertListView(ListView):
    model = BusAlert
    template_name = 'transportation/alerts.html'
    context_object_name = 'alerts'

    def get_queryset(self):
        return BusAlert.objects.filter(
            active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )

