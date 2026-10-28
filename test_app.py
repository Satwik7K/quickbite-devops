import pytest

import app as appmod


class FakeTable:
    def __init__(self):
        self.items = []

    def put_item(self, Item):
        self.items.append(Item)

    def scan(self, Limit=10):
        return {"Items": self.items[:Limit]}


@pytest.fixture
def setup(monkeypatch):
    table = FakeTable()
    monkeypatch.setattr(appmod, "get_table", lambda: table)
    appmod.app.config["TESTING"] = True
    return appmod.app.test_client(), table


def test_home_shows_name_and_version(setup):
    client, _ = setup
    body = client.get("/").get_data(as_text=True)
    assert "QuickBite" in body and appmod.VERSION in body


def test_health_is_ok(setup):
    client, _ = setup
    resp = client.get("/health")
    assert resp.status_code == 200 and resp.get_json()["status"] == "ok"


def test_menu_lists_items(setup):
    client, _ = setup
    assert "veg-burger" in client.get("/menu").get_json()


def test_order_is_saved(setup):
    client, table = setup
    resp = client.post("/order", json={"item": "veg-burger", "qty": 2})
    assert resp.status_code == 201
    assert table.items[0]["total"] == 240


def test_invalid_order_is_rejected(setup):
    client, table = setup
    assert client.post("/order", json={"item": "pizza", "qty": 1}).status_code == 400
    assert client.post("/order", json={"item": "veg-burger", "qty": 99}).status_code == 400
    assert table.items == []


def test_orders_are_listed(setup):
    client, _ = setup
    client.post("/order", json={"item": "cold-coffee", "qty": 1})
    data = client.get("/orders").get_json()
    assert data["count"] == 1


def test_demo_error_returns_500(setup):
    client, _ = setup
    assert client.get("/demo/error").status_code == 500
