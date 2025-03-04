from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q


from .models import Cafeteria, MenuItem, DailyMenu, Order, OrderItem
from .forms import OrderForm, OrderItemForm



class CafeteriaListView(ListView):
    model = Cafeteria
    template_name = 'cafeteria/cafeteria_list.html'
    context_object_name = 'cafeterias'


class CafeteriaDetailView(DetailView):
    model = Cafeteria
    template_name = 'cafeteria/cafeteria_detail.html'
    context_object_name = 'cafeteria'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        context['daily_menu'] = DailyMenu.objects.filter(cafeteria=self.object, date=today).first()
        return context


class MenuItemListView(ListView):
    model = MenuItem
    template_name = 'cafeteria/menu_items.html'
    context_object_name = 'menu_items'

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get('category')
        search = self.request.GET.get('search')

        if category:
            queryset = queryset.filter(category=category)
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(description__icontains=search))

        return queryset


class DailyMenuView(View):
    def get(self, request):
        date = request.GET.get('date', timezone.now().date())
        cafeteria_id = request.GET.get('cafeteria')

        if cafeteria_id:
            cafeteria = get_object_or_404(Cafeteria, id=cafeteria_id)
            daily_menu = DailyMenu.objects.filter(cafeteria=cafeteria, date=date).first()
            if daily_menu:
                return render(request, 'cafeteria/daily_menu.html', {'daily_menu': daily_menu})
            else:
                messages.info(request, "No menu available for this date.")
                return render(request, 'cafeteria/daily_menu.html')
        else:
            cafeterias = Cafeteria.objects.all()
            return render(request, 'cafeteria/select_cafeteria.html', {'cafeterias': cafeterias})


class CreateOrderView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'cafeteria/create_order.html'
    success_url = reverse_lazy('cafeteria:my_orders')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['orderitems'] = OrderItemForm(self.request.POST)
        else:
            context['orderitems'] = OrderItemForm()
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)

        # Process order items
        orderitems = OrderItemForm(self.request.POST)
        if orderitems.is_valid():
            items = orderitems.save(commit=False)
            for item in items:
                item.order = self.object
                item.save()

        messages.success(self.request, 'Your order has been placed successfully!')
        return response


class MyOrdersView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'cafeteria/my_orders.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'cafeteria/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


