
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction

from .models import (
    MenuItem,
    Order,
    OrderItem,
    RestaurantTable,
    Reservation,
    Inventory,
)


def read_data(request):
    try:
        return json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


# Website home page: show dishes and accept orders
def home_page(request):
    success_message = ""

    if request.method == "POST":
        customer_name = request.POST.get("customer_name", "").strip()
        selected_items = []

        for item in MenuItem.objects.filter(is_available=True):
            if request.POST.get(f"item_{item.id}"):
                try:
                    quantity = int(
                        request.POST.get(f"quantity_{item.id}", 1)
                    )
                except (ValueError, TypeError):
                    quantity = 0

                if quantity > 0:
                    selected_items.append((item, quantity))

        if customer_name and selected_items:
            with transaction.atomic():
                order = Order.objects.create(
                    customer_name=customer_name
                )

                for item, quantity in selected_items:
                    OrderItem.objects.create(
                        order=order,
                        menu_item=item,
                        quantity=quantity,
                    )

            success_message = (
                f"Order placed successfully! Order ID: {order.id}"
            )
        else:
            success_message = (
                "Enter your name and select at least one dish."
            )

    menu_items = MenuItem.objects.filter(is_available=True)

    return render(
        request,
        "restaurant/menu.html",
        {
            "menu_items": menu_items,
            "success_message": success_message,
        },
    )


# View all menu items
@require_http_methods(["GET"])
def menu_api(request):
    items = MenuItem.objects.filter(is_available=True)

    data = [
        {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "price": str(item.price),
        }
        for item in items
    ]

    return JsonResponse({"menu": data})


# View orders and create a new order using JSON
@csrf_exempt
@require_http_methods(["GET", "POST"])
def orders_api(request):
    if request.method == "GET":
        orders = Order.objects.all().order_by("-id")

        data = [
            {
                "id": order.id,
                "customer_name": order.customer_name,
                "table_id": order.table_id,
                "status": str(order.status),
                "items": [
                    {
                        "menu_item_id": oi.menu_item_id,
                        "name": oi.menu_item.name,
                        "quantity": oi.quantity,
                        "price": str(oi.menu_item.price),
                    }
                    for oi in OrderItem.objects.filter(order=order)
                ],
            }
            for order in orders
        ]

        return JsonResponse({"orders": data})

    data = read_data(request)

    if data is None:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    customer_name = str(data.get("customer_name", "")).strip()
    items = data.get("items", [])

    if not customer_name or not isinstance(items, list) or not items:
        return JsonResponse(
            {"error": "Provide customer_name and a non-empty items list"},
            status=400,
        )

    try:
        with transaction.atomic():
            order = Order.objects.create(customer_name=customer_name)

            for entry in items:
                item_id = int(entry["menu_item_id"])
                quantity = int(entry.get("quantity", 1))

                if quantity < 1:
                    raise ValueError("Quantity must be at least 1")

                menu_item = MenuItem.objects.get(
                    id=item_id,
                    is_available=True,
                )

                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=quantity,
                )

        return JsonResponse(
            {
                "message": "Order placed successfully",
                "order_id": order.id,
            },
            status=201,
        )

    except (KeyError, TypeError, ValueError, MenuItem.DoesNotExist):
        return JsonResponse(
            {"error": "Invalid menu item or quantity"},
            status=400,
        )


# View restaurant tables
@require_http_methods(["GET"])
def tables_api(request):
    tables = RestaurantTable.objects.all()

    data = [
        {
            "id": table.id,
            "table_number": table.table_number,
            "capacity": table.capacity,
            "is_available": table.is_available,
        }
        for table in tables
    ]

    return JsonResponse({"tables": data})


# View and create table reservations
@csrf_exempt
@require_http_methods(["GET", "POST"])
def reservations_api(request):
    if request.method == "GET":
        reservations = Reservation.objects.all().order_by("-id")

        data = [
            {
                "id": reservation.id,
                "customer_name": reservation.customer_name,
                "phone": reservation.phone,
                "table_id": reservation.table_id,
                "reservation_time": reservation.reservation_time.isoformat(),
                "guests": reservation.guests,
                "status": reservation.status,
            }
            for reservation in reservations
        ]

        return JsonResponse({"reservations": data})

    data = read_data(request)

    if data is None:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        customer_name = str(data["customer_name"]).strip()
        phone = str(data["phone"]).strip()
        table_id = int(data["table_id"])
        guests = int(data["guests"])
        reservation_time = data["reservation_time"]

        if not customer_name or not phone or guests < 1:
            raise ValueError("Invalid customer details")

        with transaction.atomic():
            table = RestaurantTable.objects.select_for_update().get(
                id=table_id
            )

            if not table.is_available:
                return JsonResponse(
                    {"error": "Table is not available"},
                    status=409,
                )

            if guests > table.capacity:
                return JsonResponse(
                    {"error": "Guest count exceeds table capacity"},
                    status=400,
                )

            reservation = Reservation.objects.create(
                customer_name=customer_name,
                phone=phone,
                table=table,
                reservation_time=reservation_time,
                guests=guests,
            )

            table.is_available = False
            table.save(update_fields=["is_available"])

        return JsonResponse(
            {
                "message": "Reservation created successfully",
                "reservation_id": reservation.id,
            },
            status=201,
        )

    except RestaurantTable.DoesNotExist:
        return JsonResponse({"error": "Table not found"}, status=404)
    except (KeyError, TypeError, ValueError):
        return JsonResponse(
            {"error": "Check customer details, table_id, guests and reservation_time"},
            status=400,
        )


# View inventory and update ingredient stock
@csrf_exempt
@require_http_methods(["GET", "PATCH"])
def inventory_api(request):
    if request.method == "GET":
        items = Inventory.objects.all()

        data = [
            {
                "id": item.id,
                "ingredient_name": item.ingredient_name,
                "quantity": str(item.quantity),
                "unit": item.unit,
                "low_stock_limit": str(item.low_stock_limit),
            }
            for item in items
        ]

        return JsonResponse({"inventory": data})

    data = read_data(request)

    if data is None:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        item_id = int(data["id"])
        quantity = float(data["quantity"])

        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

        item = Inventory.objects.get(id=item_id)
        item.quantity = quantity
        item.save(update_fields=["quantity"])

        return JsonResponse(
            {
                "message": "Inventory updated successfully",
                "id": item.id,
                "ingredient_name": item.ingredient_name,
                "quantity": str(item.quantity),
                "unit": item.unit,
            }
        )

    except Inventory.DoesNotExist:
        return JsonResponse({"error": "Inventory item not found"}, status=404)
    except (KeyError, TypeError, ValueError):
        return JsonResponse(
            {"error": "Provide a valid inventory id and quantity"},
            status=400,
        )
