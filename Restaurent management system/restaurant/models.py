
from django.db import models


class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class RestaurantTable(models.Model):
    table_number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveIntegerField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Table {self.table_number}"


class Reservation(models.Model):
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    table = models.ForeignKey(
        RestaurantTable,
        on_delete=models.CASCADE
    )
    reservation_time = models.DateTimeField()
    guests = models.PositiveIntegerField()
    status = models.CharField(max_length=20, default="Booked")

    def __str__(self):
        return self.customer_name


class Order(models.Model):
    customer_name = models.CharField(max_length=100)
    table = models.ForeignKey(
        RestaurantTable,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    items = models.ManyToManyField(MenuItem, through="OrderItem")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Pending")

    def __str__(self):
        return f"Order {self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


class Inventory(models.Model):
    ingredient_name = models.CharField(max_length=100, unique=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    low_stock_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=5
    )

    def __str__(self):
        return self.ingredient_name
