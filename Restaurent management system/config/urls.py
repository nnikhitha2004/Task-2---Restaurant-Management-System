
from django.contrib import admin
from django.urls import path, include
from restaurant import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_page, name='home'),
    path('api/', include('restaurant.urls')),
]
