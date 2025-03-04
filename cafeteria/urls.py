# cafeteria/urls.py
from django.urls import path
from .views import (
    CafeteriaListView,
    CafeteriaDetailView,
    MenuItemListView,
    DailyMenuView,
    CreateOrderView,
    MyOrdersView,
    OrderDetailView,
)

app_name = 'cafeteria'  # Namespace for the app

urlpatterns = [
    # Cafeteria URLs
    path('', CafeteriaListView.as_view(), name='cafeteria_list'),
    path('<int:pk>/', CafeteriaDetailView.as_view(), name='cafeteria_detail'),

    # Menu Item URLs
    path('menu-items/', MenuItemListView.as_view(), name='menu_item_list'),

    # Daily Menu URL
    path('daily-menu/', DailyMenuView.as_view(), name='daily_menu'),

    # Order URLs
    path('create-order/', CreateOrderView.as_view(), name='create_order'),
    path('my-orders/', MyOrdersView.as_view(), name='my_orders'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
]