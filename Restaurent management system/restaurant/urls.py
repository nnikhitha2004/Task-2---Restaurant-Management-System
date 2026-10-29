
from django.urls import path
from . import views

urlpatterns = [
    path('menu/', views.menu_api, name='menu'),
    path('orders/', views.orders_api, name='orders'),
    path('tables/', views.tables_api, name='tables'),
    path('reservations/', views.reservations_api, name='reservations'),
    path('inventory/', views.inventory_api, name='inventory'),
]
