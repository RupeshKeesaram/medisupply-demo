"""HTTP acceptance of the documented application contract, using temporary storage."""
from __future__ import annotations

import copy
import http.cookiejar
import json
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import Handler, build_server
from store import Store


class Client:
    def __init__(self, origin):
        self.origin = origin
        self.cookies = http.cookiejar.CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.cookies))

    def call(self, method, path, body=None, headers=None, raw=None):
        payload = raw if raw is not None else json.dumps(body).encode() if body is not None else None
        request = Request(self.origin + path, data=payload, method=method,
                          headers={"Content-Type": "application/json", **(headers or {})})
        try:
            response = self.opener.open(request, timeout=10)
        except HTTPError as error:
            response = error
        with response:
            raw_response = response.read()
            data = json.loads(raw_response) if response.headers.get_content_type() == "application/json" else raw_response.decode()
            return response.status, data

    def login(self, email="buyer@greenfield.demo"):
        return self.call("POST", "/api/login", {"email": email, "password": "MediSupply2026!"})

    def quote(self, quantity=1, product="amoxicillin", code=""):
        return self.call("POST", "/api/quote", {"items": [{"product_id": product, "quantity": quantity}], "discount_code": code})

    def order(self, quantity=1, key="acceptance-order-0001", items=None):
        return self.call("POST", "/api/orders", {"items": items if items is not None else [{"product_id": "amoxicillin", "quantity": quantity}],
                                                "purchase_order": "GF-TEST-001", "idempotency_key": key})

    def stock(self, pid="amoxicillin"):
        return next(p["stock"] for p in self.call("GET", "/api/catalog")[1]["products"] if p["id"] == pid)


class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.database = str(Path(cls.temp.name) / "data.sqlite3")
        cls.old_log = Handler.log_message
        Handler.log_message = lambda *args: None
        cls.server = build_server(port=0, db_path=cls.database)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        Handler.log_message = cls.old_log
        cls.temp.cleanup()

    def setUp(self):
        self.client = Client(self.origin)

    def test_health_and_direct_page_routes(self):
        status, data = self.client.call("GET", "/health")
        self.assertEqual((status, data["status"]), (200, "ok"))
        self.assertEqual(len(data["commit"]), 40)
        for path in ["/", "/login", "/dashboard", "/catalog", "/cart", "/inventory", "/orders", "/orders/MS-1046"]:
            with self.subTest(path=path):
                status, html = self.client.call("GET", path)
                self.assertEqual(status, 200)
                self.assertIn("MediSupply", html)

    def test_sign_in_role_and_sign_out(self):
        self.assertEqual(self.client.call("GET", "/api/inventory")[0], 401)
        status, data = self.client.login()
        self.assertEqual(status, 200)
        self.assertEqual(data["user"]["role"], "pharmacy")
        self.assertEqual(self.client.call("GET", "/api/session")[1]["user"]["id"], "greenfield")
        self.assertEqual(self.client.call("POST", "/api/logout", {})[0], 200)
        self.assertEqual(self.client.call("GET", "/api/orders")[0], 401)

    def test_bad_credentials_and_client_role(self):
        for password in ["wrong", "💊", None, 123]:
            with self.subTest(password=password):
                self.assertEqual(self.client.call("POST", "/api/login", {"email": "buyer@greenfield.demo", "password": password})[0], 401)
        status, data = self.client.call("POST", "/api/login", {"email": "buyer@greenfield.demo", "password": "MediSupply2026!", "role": "admin"})
        self.assertEqual((status, data["user"]["role"]), (200, "pharmacy"))

    def test_catalog_search_and_combined_filters(self):
        self.assertEqual(self.client.call("GET", "/api/catalog")[1]["total"], 12)
        self.assertEqual(self.client.call("GET", "/api/catalog?q=%20MED-1001%20")[1]["products"][0]["id"], "amoxicillin")
        self.assertEqual(self.client.call("GET", "/api/catalog?q=AMOXICILLIN&category=Antibiotics")[1]["total"], 1)
        self.assertEqual(self.client.call("GET", "/api/catalog?q=Amoxicillin&category=Cardiovascular")[1]["total"], 0)
        self.assertEqual(self.client.call("GET", "/api/catalog?availability=expired")[1]["products"][0]["id"], "azithromycin")

    def test_invalid_quantity_types(self):
        for quantity in [0, -1, -120, 1.5, "2", True, None, 10001]:
            with self.subTest(quantity=quantity):
                status, data = self.client.quote(quantity)
                self.assertEqual(status, 400)
                self.assertEqual(data["code"], "invalid_quantity")

    def test_exact_stock_and_excess_stock(self):
        self.assertEqual(self.client.quote(100)[0], 200)
        for quantity in [101, 120]:
            with self.subTest(quantity=quantity):
                status, data = self.client.quote(quantity)
                self.assertEqual((status, data.get("code")), (400, "insufficient_stock"))
        self.assertEqual(self.client.stock(), 100)

    def test_duplicate_lines_aggregate_stock(self):
        status, _ = self.client.call("POST", "/api/quote", {"items": [{"product_id": "amoxicillin", "quantity": 60}, {"product_id": "amoxicillin", "quantity": 60}]})
        self.assertEqual(status, 400)
        status, data = self.client.call("POST", "/api/quote", {"items": [{"product_id": "amoxicillin", "quantity": 40}, {"product_id": "amoxicillin", "quantity": 60}]})
        self.assertEqual((status, len(data["lines"]), data["lines"][0]["quantity"]), (200, 1, 100))

    def test_expired_and_unavailable_products(self):
        for pid in ["azithromycin", "salbutamol"]:
            with self.subTest(product=pid):
                self.assertEqual(self.client.quote(1, pid)[0], 400)
        self.client.login()
        self.assertEqual(self.client.call("PUT", "/api/cart", {"items": [{"product_id": "azithromycin", "quantity": 1}]})[0], 400)
        self.assertEqual(self.client.order(items=[{"product_id": "azithromycin", "quantity": 1}])[0], 400)

    def test_price_discount_and_aggregate_rounding(self):
        cases = [([{"product_id": "amoxicillin", "quantity": 10}], 12500, 1250, 11250),
                 ([{"product_id": "cetirizine", "quantity": 3}], 1425, 143, 1282),
                 ([{"product_id": "amoxicillin", "quantity": 2}, {"product_id": "cetirizine", "quantity": 3}], 3925, 393, 3532)]
        for items, subtotal, discount, total in cases:
            with self.subTest(items=items):
                status, data = self.client.call("POST", "/api/quote", {"items": items, "discount_code": " care10 "})
                self.assertEqual(status, 200)
                self.assertEqual((data["subtotal_cents"], data["discount_cents"], data["total_cents"]), (subtotal, discount, total))

    def test_invalid_payloads(self):
        for body in [None, {}, {"items": []}, {"items": "wrong"}, {"items": [{}]}, {"items": [1]}, {"items": [{"product_id": [], "quantity": 1}]}]:
            with self.subTest(body=body):
                self.assertEqual(self.client.call("POST", "/api/quote", body)[0], 400)
        self.assertEqual(self.client.quote(1, "does-not-exist")[0], 404)
        self.assertEqual(self.client.call("POST", "/api/quote", raw=b"{broken")[0], 400)
        self.assertEqual(self.client.call("POST", "/api/quote", raw=b"[]")[0], 400)
        self.assertEqual(self.client.quote(1, code="UNKNOWN")[0], 400)

    def test_cart_discount_reapplication_and_removal(self):
        self.client.login()
        body = {"items": [{"product_id": "amoxicillin", "quantity": 10}], "discount_code": "CARE10"}
        first = self.client.call("PUT", "/api/cart", body)
        second = self.client.call("PUT", "/api/cart", body)
        self.assertEqual(first, second)
        self.assertEqual(first[1]["total_cents"], 11250)
        body["discount_code"] = "INVALID"
        self.assertEqual(self.client.call("PUT", "/api/cart", body)[0], 400)
        self.assertEqual(self.client.call("GET", "/api/cart")[1], first[1])
        body["discount_code"] = ""
        self.assertEqual(self.client.call("PUT", "/api/cart", body)[1]["total_cents"], 12500)
        self.assertEqual(self.client.stock(), 100)

    def test_submit_reserves_stock_and_idempotent_replay(self):
        self.client.login()
        status, result = self.client.order(10)
        self.assertEqual(status, 201)
        self.assertEqual(result["order"]["status"], "submitted")
        self.assertEqual(self.client.stock(), 90)
        self.assertEqual(self.client.order(10), (200, result))
        self.assertEqual(self.client.stock(), 90)
        self.assertEqual(self.client.call("GET", "/api/cart")[1]["lines"], [])
        self.assertEqual(len(self.client.call("GET", "/api/orders")[1]["orders"]), 7)

    def test_order_pricing_matches_cart_and_receipt(self):
        self.client.login()
        _, cart = self.client.call("PUT", "/api/cart", {"items": [{"product_id": "amoxicillin", "quantity": 10}], "discount_code": "CARE10"})
        status, result = self.client.call("POST", "/api/orders", {"purchase_order": "GF-PRICING-001", "idempotency_key": "cart-submit-001"})
        self.assertEqual(status, 201)
        self.assertEqual(result["order"]["total_cents"], cart["total_cents"])
        self.assertEqual(result["order"]["total_cents"], 11250)
        self.assertEqual(self.client.call("GET", "/api/orders/" + result["order"]["id"])[1]["order"], result["order"])

    def test_invalid_order_is_atomic(self):
        self.client.login()
        before = self.client.call("GET", "/api/orders")[1]
        status, _ = self.client.order(items=[{"product_id": "amoxicillin", "quantity": 5}, {"product_id": "metformin", "quantity": 241}])
        self.assertEqual(status, 400)
        self.assertEqual(self.client.stock(), 100)
        self.assertEqual(self.client.call("GET", "/api/orders")[1], before)
        self.assertEqual(self.client.order(1)[1]["order"]["id"], "MS-1049")

    def test_invalid_submission_details(self):
        self.client.login()
        base = {"items": [{"product_id": "amoxicillin", "quantity": 1}], "purchase_order": "valid", "idempotency_key": "request-0001"}
        for key, value in [("purchase_order", " "), ("purchase_order", "x" * 61), ("notes", "x" * 501), ("idempotency_key", "")]:
            with self.subTest(key=key):
                self.assertEqual(self.client.call("POST", "/api/orders", {**base, key: value})[0], 400)
        self.assertEqual(self.client.stock(), 100)

    def test_stock_rechecked_at_submission(self):
        self.client.login("admin@medisupply.demo")
        self.assertEqual(self.client.call("PUT", "/api/cart", {"items": [{"product_id": "amoxicillin", "quantity": 10}]})[0], 200)
        self.client.call("PATCH", "/api/inventory", {"product_id": "amoxicillin", "stock": 5, "reason": "Stock recount"})
        self.assertEqual(self.client.order(10)[0], 400)
        self.assertEqual(self.client.stock(), 5)

    def test_inventory_requires_administrator(self):
        body = {"product_id": "amoxicillin", "stock": 80, "reason": "Warehouse receipt"}
        self.assertEqual(self.client.call("PATCH", "/api/inventory", body)[0], 401)
        self.client.login()
        self.assertEqual(self.client.call("PATCH", "/api/inventory", body)[0], 403)
        self.assertEqual(self.client.stock(), 100)

    def test_inventory_adjustment_and_alerts(self):
        self.client.login("admin@medisupply.demo")
        status, result = self.client.call("PATCH", "/api/inventory", {"product_id": "amoxicillin", "stock": 15, "reason": "Cycle count"})
        self.assertEqual(status, 200)
        self.assertEqual(result["product"]["availability"], "low_stock")
        self.assertEqual((result["adjustment"]["before"], result["adjustment"]["after"]), (100, 15))
        self.assertEqual(self.client.call("GET", "/api/inventory")[1]["history"][0]["by"], "Jordan Ellis")
        self.assertIn("amoxicillin", [p["id"] for p in self.client.call("GET", "/api/dashboard")[1]["alerts"]])
        for stock in [-1, 100001, True, 1.5]:
            with self.subTest(stock=stock):
                self.assertEqual(self.client.call("PATCH", "/api/inventory", {"product_id": "amoxicillin", "stock": stock, "reason": "Count"})[0], 400)

    def test_order_visibility_and_admin_scope(self):
        self.client.login()
        self.assertEqual(self.client.call("GET", "/api/orders/MS-1042")[0], 404)
        self.assertEqual(self.client.call("POST", "/api/orders/cancel", {"order_id": "MS-1042"})[0], 404)
        self.client.login("buyer@riverside.demo")
        self.assertEqual(len(self.client.call("GET", "/api/orders")[1]["orders"]), 1)
        self.assertEqual(self.client.call("GET", "/api/orders/MS-1048")[0], 404)
        self.client.login("admin@medisupply.demo")
        self.assertEqual(len(self.client.call("GET", "/api/orders")[1]["orders"]), 7)

    def test_cancellation_releases_stock_once(self):
        self.client.login()
        order_id = self.client.order(10)[1]["order"]["id"]
        self.assertEqual(self.client.stock(), 90)
        status, result = self.client.call("POST", "/api/orders/cancel", {"order_id": order_id})
        self.assertEqual((status, result["order"]["status"]), (200, "cancelled"))
        self.assertEqual(self.client.stock(), 100)
        self.assertEqual(self.client.call("POST", "/api/orders/cancel", {"order_id": order_id})[0], 409)
        self.assertEqual(self.client.stock(), 100)

    def test_shipped_delivered_and_cancelled_are_final_for_cancellation(self):
        self.client.login()
        for order_id in ["MS-1046", "MS-1045", "MS-1043"]:
            with self.subTest(order=order_id):
                before = self.client.call("GET", "/api/orders/" + order_id)[1]
                self.assertEqual(self.client.call("POST", "/api/orders/cancel", {"order_id": order_id})[0], 409)
                self.assertEqual(self.client.call("GET", "/api/orders/" + order_id)[1], before)

    def test_admin_fulfillment_sequence(self):
        self.client.login()
        body = {"order_id": "MS-1048", "status": "processing"}
        self.assertEqual(self.client.call("PATCH", "/api/orders/status", body)[0], 403)
        self.client.login("admin@medisupply.demo")
        self.assertEqual(self.client.call("PATCH", "/api/orders/status", {**body, "status": "delivered"})[0], 409)
        for status in ["processing", "shipped", "delivered"]:
            code, result = self.client.call("PATCH", "/api/orders/status", {**body, "status": status})
            self.assertEqual((code, result["order"]["status"]), (200, status))
        self.assertEqual(len(result["order"]["history"]), 4)
        self.assertTrue(result["order"]["tracking_reference"])

    def test_dashboard_totals_match_visible_orders(self):
        self.client.login()
        metrics = self.client.call("GET", "/api/dashboard")[1]["metrics"]
        orders = self.client.call("GET", "/api/orders")[1]["orders"]
        self.assertEqual(metrics["open_orders"], 2)
        self.assertEqual(metrics["in_transit"], 1)
        self.assertEqual(metrics["inventory_alerts"], 4)
        self.assertEqual(metrics["order_value_cents"], sum(o["total_cents"] for o in orders if o["status"] != "cancelled"))

    def test_fresh_browser_isolation_and_storage_reopen(self):
        self.client.login()
        self.client.order(10)
        self.assertEqual(Client(self.origin).stock(), 100)
        sid = next(c.value for c in self.client.cookies if c.name.startswith("medisupply_workspace_"))
        reopened = Store(self.database)
        with reopened.workspace(sid) as (_, world, fresh):
            self.assertFalse(fresh)
            self.assertEqual(world["products"]["amoxicillin"]["stock"], 90)
            self.assertEqual(world["orders"][0]["id"], "MS-1049")

    def test_concurrent_requests_cannot_oversell(self):
        self.client.login()
        def submit(number):
            client = Client(self.origin)
            for cookie in self.client.cookies:
                client.cookies.set_cookie(copy.copy(cookie))
            return client.order(60, f"concurrent-order-{number}")[0]
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(submit, [1, 2]))
        self.assertEqual(sorted(statuses), [201, 400])
        self.assertEqual(self.client.stock(), 40)

    def test_cross_site_and_path_traversal_rejected(self):
        self.client.login()
        self.assertEqual(self.client.call("POST", "/api/logout", {}, headers={"Origin": "https://elsewhere.invalid"})[0], 403)
        self.assertIsNotNone(self.client.call("GET", "/api/session")[1]["user"])
        self.assertEqual(self.client.call("GET", "/static/../server.py")[0], 404)

    def test_public_authorities_keep_sessions_separate(self):
        self.client.login()
        self.assertIsNotNone(self.client.call("GET", "/api/session")[1]["user"])
        status, data = self.client.call("GET", "/api/session", headers={"Host": "localhost:other-preview"})
        self.assertEqual(status, 200)
        self.assertIsNone(data["user"])
        self.assertIsNotNone(self.client.call("GET", "/api/session")[1]["user"])


if __name__ == "__main__":
    unittest.main()
