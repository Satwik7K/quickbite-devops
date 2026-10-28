import logging
import os
import time
import uuid

import boto3
from flask import Flask, jsonify, request

VERSION = "1.0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("quickbite")

app = Flask(__name__)

MENU = {
    "veg-burger": {"name": "Veg Burger", "price": 120},
    "paneer-wrap": {"name": "Paneer Wrap", "price": 150},
    "masala-fries": {"name": "Masala Fries", "price": 90},
    "cold-coffee": {"name": "Cold Coffee", "price": 80},
}


def get_table():
    """Return the DynamoDB table that stores orders (credentials come from the ECS task role)."""
    name = os.environ.get("TABLE_NAME", "quickbite-orders-dev")
    region = os.environ.get("AWS_REGION", "ap-south-1")
    return boto3.resource("dynamodb", region_name=region).Table(name)


def plain(item):
    """Convert DynamoDB numbers (Decimal) to plain ints so they can be returned as JSON."""
    return {k: (int(v) if hasattr(v, "as_tuple") else v) for k, v in item.items()}


@app.route("/")
def home():
    return f"QuickBite online food ordering - Version {VERSION}\n"


@app.route("/health")
def health():
    return jsonify(status="ok", version=VERSION)


@app.route("/menu")
def menu():
    return jsonify(MENU)


@app.route("/order", methods=["POST"])
def order():
    data = request.get_json(silent=True) or {}
    item = data.get("item")
    qty = data.get("qty", 1)
    if item not in MENU or not isinstance(qty, int) or not 1 <= qty <= 20:
        return jsonify(error="send JSON like {\"item\": \"veg-burger\", \"qty\": 2}"), 400
    order_id = uuid.uuid4().hex[:8]
    record = {
        "orderId": order_id,
        "item": item,
        "qty": qty,
        "total": MENU[item]["price"] * qty,
        "createdAt": int(time.time()),
    }
    get_table().put_item(Item=record)
    log.info("order placed id=%s item=%s qty=%s", order_id, item, qty)
    return jsonify(record), 201


@app.route("/orders")
def orders():
    items = get_table().scan(Limit=10).get("Items", [])
    return jsonify(count=len(items), orders=[plain(i) for i in items])


@app.route("/demo/error")
def demo_error():
    """Used only to demonstrate monitoring: writes an ERROR log line that triggers a CloudWatch alarm."""
    log.error("ERROR simulated failure for the monitoring demo")
    return jsonify(error="simulated failure"), 500
