
from django.contrib import admin
from .models import (
    MenuItem,
    RestaurantTable,
    Reservation,
    Order,
    OrderItem,
    Inventory,
)

admin.site.register(MenuItem)
admin.site.register(RestaurantTable)
admin.site.register(Reservation)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Inventory)
