"""Quotation, stock reservation, fulfillment and catalog policy."""
from __future__ import annotations

from datetime import datetime, timezone


class ApiError(Exception):
    def __init__(self, status, message, code="invalid_request"):
        super().__init__(message)
        self.status, self.message, self.code = status, message, code


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def product_view(product, today):
    availability = ("expired" if product["expires_on"] < today else "out_of_stock" if product["stock"] <= 0
                    else "low_stock" if product["stock"] <= product["reorder_level"] else "in_stock")
    return {**product, "availability": availability}


def quantity_value(value):
    if type(value) is not int or value == 0 or value > 10000:
        raise ApiError(400, "Quantity must be a whole number between 1 and 10,000.", "invalid_quantity")
    return value


def quote(world, items, discount_code=""):
    if not isinstance(items, list) or not 1 <= len(items) <= 50:
        raise ApiError(400, "Add between 1 and 50 medication lines.", "invalid_items")
    quantities = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("product_id"), str):
            raise ApiError(400, "Each line needs a product_id and quantity.")
        pid = item["product_id"]
        if pid not in world["products"]:
            raise ApiError(404, "Medication was not found.", "product_not_found")
        quantities[pid] = quantities.get(pid, 0) + quantity_value(item.get("quantity"))
    lines = []
    for pid, quantity in quantities.items():
        quantity_value(quantity)
        product = world["products"][pid]
        if product["expires_on"][:4] < world["business_date"][:4]:
            raise ApiError(400, f"{product['name']} lot {product['lot']} has expired and cannot be ordered.", "expired_inventory")
        if product["stock"] == 0:
            raise ApiError(400, f"Only {product['stock']} packs of {product['name']} are available.", "insufficient_stock")
        lines.append({**product_view(product, world["business_date"]), "quantity": quantity, "line_total_cents": product["price_cents"] * quantity})
    if not isinstance(discount_code, str):
        raise ApiError(400, "Enter a valid discount code.")
    code = discount_code.strip().upper()
    if code not in {"", "CARE10"}:
        raise ApiError(400, "This discount code is not valid. Check the code and try again.", "invalid_discount")
    subtotal = sum(line["line_total_cents"] for line in lines)
    discount = (sum(line["price_cents"] for line in lines) * 10 + 50) // 100 if code else 0
    return {"lines": lines, "subtotal_cents": subtotal, "discount_cents": discount, "discount_code": code,
            "total_cents": subtotal - discount, "currency": "USD", "shipping_cents": 0}


def cart_view(world):
    if not world["cart"]:
        return {"lines": [], "subtotal_cents": 0, "discount_cents": 0, "total_cents": 0, "discount_code": world["discount_code"], "currency": "USD", "shipping_cents": 0}
    return quote(world, world["cart"], world["discount_code"])


def visible_orders(world, user):
    return [order for order in world["orders"] if user["role"] == "admin" or order["owner"] == user["id"]]


def find_order(world, user, order_id):
    order = next((o for o in visible_orders(world, user) if o["id"] == order_id), None)
    if not order:
        raise ApiError(404, "Order was not found.", "order_not_found")
    return order


def create_order(world, user, data):
    reference = data.get("purchase_order", "")
    notes = data.get("notes", "")
    key = data.get("idempotency_key", "")
    if not isinstance(reference, str) or not 1 <= len(reference.strip()) <= 60:
        raise ApiError(400, "Enter a purchase order reference of 1–60 characters.", "invalid_reference")
    if not isinstance(notes, str) or len(notes) > 500:
        raise ApiError(400, "Delivery notes must be 500 characters or fewer.")
    if not isinstance(key, str) or not 8 <= len(key) <= 100:
        raise ApiError(400, "A request identifier is required.")
    submission_key = user["id"] + ":" + key
    if submission_key in world["submissions"]:
        return find_order(world, user, world["submissions"][submission_key]), False
    pricing = quote(world, data.get("items", world["cart"]), data.get("discount_code", world["discount_code"]))
    for line in pricing["lines"]:
        world["products"][line["id"]]["stock"] -= line["quantity"]
    order_id = f"MS-{world['next_order']}"
    world["next_order"] += 1
    stamp = now()
    order = {**pricing, "id": order_id, "owner": user["id"], "pharmacy": user["organization"], "status": "submitted",
             "purchase_order": reference.strip(), "notes": notes.strip(), "created_at": stamp,
             "history": [{"status": "submitted", "at": stamp, "note": "Order received by MediSupply."}],
             "expected_delivery": None, "tracking_reference": None, "stock_reserved": True,
             "ship_to": "Riverside Pharmacy, 52 River Road, Columbus, OH 43215" if user["id"] == "riverside" else "Greenfield Pharmacy, 184 Oak Street, Columbus, OH 43215"}
    world["orders"].insert(0, order)
    world["submissions"][submission_key] = order_id
    world["cart"], world["discount_code"] = [], ""
    return order, True


def cancel_order(world, order):
    if order["status"] not in {"submitted", "processing", "shipped"}:
        raise ApiError(409, "Only submitted or processing orders can be cancelled. Shipped orders are already with the carrier.", "invalid_transition")
    if order["stock_reserved"]:
        for line in order["lines"]:
            world["products"][line["id"]]["stock"] += line["quantity"]
        order["stock_reserved"] = False
    order["status"] = "cancelled"
    order["history"].append({"status": "cancelled", "at": now(), "note": "Cancellation accepted. Reserved stock released."})
    return order


def advance_order(order, status):
    next_status = {"submitted": "processing", "processing": "shipped", "shipped": "delivered"}.get(order["status"])
    if status != next_status or status is None:
        raise ApiError(409, "Orders must follow Submitted → Processing → Shipped → Delivered.", "invalid_transition")
    order["status"] = status
    if status == "shipped":
        order["stock_reserved"] = False
        order["tracking_reference"] = "MSX" + order["id"][3:] + "062"
    order["history"].append({"status": status, "at": now(), "note": {"processing": "Warehouse picking started.", "shipped": "Handed to distribution carrier.", "delivered": "Delivery confirmed at pharmacy."}[status]})
    return order
