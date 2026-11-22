"""MediSupply HTTP application. Python standard library; SQLite persistence."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from orders import ApiError, advance_order, cancel_order, cart_view, create_order, find_order, now, product_view, quote, visible_orders
from store import ACCOUNTS, PASSWORD, Store

ROOT = Path(__file__).resolve().parent
PAGES = re.compile(r"^/(?:login|dashboard|catalog|cart|inventory|orders(?:/MS-\d+)?)?/?$")


class Handler(BaseHTTPRequestHandler):
    server_version = "MediSupply"

    def log_message(self, fmt, *args):
        if args and isinstance(args[0], str) and "/health" in args[0]:
            return
        super().log_message(fmt, *args)

    def respond(self, status, body, content_type="application/json; charset=utf-8"):
        raw = json.dumps(body, ensure_ascii=False).encode() if isinstance(body, (dict, list)) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store" if content_type.startswith(("application/json", "text/html")) else "public, max-age=3600")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'")
        for cookie in self.pending_cookies:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(raw)

    def cookie(self, name):
        parsed = SimpleCookie()
        try:
            parsed.load(self.headers.get("Cookie", ""))
            return parsed[name].value if name in parsed else None
        except Exception:
            return None

    def set_cookie(self, name, value, age=86400):
        secure = "; Secure" if os.environ.get("MEDISUPPLY_SECURE_COOKIES") == "1" else ""
        self.pending_cookies.append(f"{name}={value}; HttpOnly; SameSite=Lax; Path=/; Max-Age={age}{secure}")

    def body(self):
        try:
            size = int(self.headers.get("Content-Length", 0))
        except ValueError:
            raise ApiError(400, "Invalid request length.")
        if not 0 <= size <= 65536:
            raise ApiError(413, "Request is too large.")
        if not size:
            return {}
        if self.headers.get_content_type() != "application/json":
            raise ApiError(415, "Send JSON using Content-Type: application/json.")
        try:
            data = json.loads(self.rfile.read(size))
        except (ValueError, UnicodeError):
            raise ApiError(400, "The request body must be valid JSON.")
        if not isinstance(data, dict):
            raise ApiError(400, "The request body must be a JSON object.")
        return data

    def user(self, world):
        token = self.cookie(self.auth_cookie)
        if not world["user"] or not token or not world["auth"] or not hmac.compare_digest(token.encode(), world["auth"].encode()) or time.time()-world["signed_in_at"] > 8*3600:
            raise ApiError(401, "Sign in to continue.", "sign_in_required")
        return world["user"]

    def admin(self, world):
        user = self.user(world)
        if user["role"] != "admin":
            raise ApiError(403, "Only an administrator can make this change.", "admin_required")
        return user

    def dispatch(self, world, method, path, data, query):
        if method == "GET" and path == "/api/session":
            try:
                user = self.user(world)
            except ApiError:
                user = None
            return 200, {"user": user, "business_date": world["business_date"]}
        if method == "POST" and path == "/api/login":
            email, password = data.get("email"), data.get("password")
            if not isinstance(email, str) or not isinstance(password, str) or email.lower().strip() not in ACCOUNTS or not hmac.compare_digest(password.encode(), PASSWORD.encode()):
                raise ApiError(401, "Email or password is incorrect.", "invalid_credentials")
            account = {**ACCOUNTS[email.lower().strip()], "email": email.lower().strip()}
            if world["user"] and world["user"]["id"] != account["id"]:
                world["cart"], world["discount_code"] = [], ""
            world.update(user=account, auth=secrets.token_urlsafe(32), signed_in_at=time.time())
            self.set_cookie(self.auth_cookie, world["auth"], 8*3600)
            return 200, {"user": account}
        if method == "POST" and path == "/api/logout":
            world.update(user=None, auth=None, cart=[], discount_code="")
            self.set_cookie(self.auth_cookie, "", 0)
            return 200, {"ok": True}
        if method == "GET" and path == "/api/catalog":
            products = [product_view(p, world["business_date"]) for p in world["products"].values()]
            search = query.get("q", [""])[0].strip().lower()
            category, manufacturer, availability = (query.get(k, [""])[0] for k in ("category", "manufacturer", "availability"))
            filtered = [p for p in products if (not search or search in (p["name"] + " " + p["code"] + " " + p["strength"]).lower())
                        and (not category or p["category"] == category) and (not manufacturer or p["manufacturer"] == manufacturer)
                        and (not availability or p["availability"] == availability)]
            return 200, {"products": filtered, "total": len(filtered), "categories": sorted({p["category"] for p in products}),
                         "manufacturers": sorted({p["manufacturer"] for p in products}), "business_date": world["business_date"]}
        if method == "POST" and path == "/api/quote":
            return 200, quote(world, data.get("items"), data.get("discount_code", ""))

        user = self.user(world)
        if method == "GET" and path == "/api/dashboard":
            orders = visible_orders(world, user)
            products = [product_view(p, world["business_date"]) for p in world["products"].values()]
            alerts = [p for p in products if p["availability"] != "in_stock"]
            return 200, {"orders": orders[:5], "alerts": alerts, "metrics": {"open_orders": sum(o["status"] in {"submitted", "processing"} for o in orders),
                         "in_transit": sum(o["status"] == "shipped" for o in orders), "inventory_alerts": len(alerts),
                         "order_value_cents": sum(o["total_cents"] for o in orders if o["status"] != "cancelled")}, "business_date": world["business_date"]}
        if method == "GET" and path == "/api/cart":
            return 200, cart_view(world)
        if method == "PUT" and path == "/api/cart":
            items = data.get("items")
            code = data.get("discount_code", world["discount_code"])
            if items == []:
                world["cart"], world["discount_code"] = [], ""
            else:
                priced = quote(world, items, code)
                world["cart"] = [{"product_id": line["id"], "quantity": line["quantity"]} for line in priced["lines"]]
                world["discount_code"] = priced["discount_code"]
            return 200, cart_view(world)
        if method == "GET" and path == "/api/orders":
            return 200, {"orders": visible_orders(world, user)}
        if method == "POST" and path == "/api/orders":
            order, created = create_order(world, user, data)
            return (201 if created else 200), {"order": order}
        if method == "GET" and path.startswith("/api/orders/"):
            return 200, {"order": find_order(world, user, path.removeprefix("/api/orders/"))}
        if method == "POST" and path == "/api/orders/cancel":
            return 200, {"order": cancel_order(world, find_order(world, user, data.get("order_id")))}
        if method == "PATCH" and path == "/api/orders/status":
            self.admin(world)
            return 200, {"order": advance_order(find_order(world, user, data.get("order_id")), data.get("status"))}
        if method == "GET" and path == "/api/inventory":
            return 200, {"products": [product_view(p, world["business_date"]) for p in world["products"].values()], "history": world["inventory_history"][-20:][::-1]}
        if method == "PATCH" and path == "/api/inventory":
            self.user(world)
            pid, stock, reason = data.get("product_id"), data.get("stock"), data.get("reason", "")
            if not isinstance(pid, str) or pid not in world["products"]:
                raise ApiError(404, "Medication was not found.")
            if type(stock) is not int or not 0 <= stock <= 100000:
                raise ApiError(400, "Stock must be a whole number between 0 and 100,000.")
            if not isinstance(reason, str) or not 3 <= len(reason.strip()) <= 200:
                raise ApiError(400, "Add an adjustment reason of 3–200 characters.")
            product = world["products"][pid]
            change = {"product_id": pid, "name": product["name"], "before": product["stock"], "after": stock, "reason": reason.strip(), "by": user["name"], "at": now()}
            product["stock"] = stock
            world["inventory_history"].append(change)
            return 200, {"product": product_view(product, world["business_date"]), "adjustment": change}
        raise ApiError(404, "This endpoint was not found.", "not_found")

    def handle_request(self):
        self.pending_cookies = []
        authority = self.headers.get("Host") or f"localhost:{self.server.server_port}"
        cookie_scope = hashlib.sha256(authority.lower().encode()).hexdigest()[:10]
        self.workspace_cookie = f"medisupply_workspace_{cookie_scope}"
        self.auth_cookie = f"medisupply_auth_{cookie_scope}"
        parsed = urlsplit(self.path)
        path, method = parsed.path, self.command
        try:
            if method in {"GET", "HEAD"} and path in {"/health", "/version"}:
                return self.respond(200, {"status": "ok", "application": "MediSupply", "commit": self.server.build_id})
            if method in {"GET", "HEAD"} and not path.startswith("/api/"):
                if PAGES.fullmatch(path):
                    asset = ROOT / "static" / "index.html"
                elif path.startswith("/static/"):
                    asset = (ROOT / path.lstrip("/")).resolve()
                    if not asset.is_relative_to((ROOT / "static").resolve()) or not asset.is_file():
                        raise ApiError(404, "Asset was not found.")
                else:
                    raise ApiError(404, "Page was not found.")
                content_type = mimetypes.guess_type(str(asset))[0] or "application/octet-stream"
                if asset.suffix == ".js":
                    content_type = "text/javascript"
                return self.respond(200, asset.read_bytes(), content_type + ("; charset=utf-8" if content_type.startswith("text/") else ""))
            if method not in {"GET", "HEAD"}:
                origin = self.headers.get("Origin")
                if self.headers.get("Sec-Fetch-Site") == "cross-site" or (origin and urlsplit(origin).netloc != self.headers.get("Host")):
                    raise ApiError(403, "Cross-site requests are not accepted.")
            data = self.body() if method not in {"GET", "HEAD"} else {}
            with self.server.store.workspace(self.cookie(self.workspace_cookie)) as (sid, world, fresh):
                status, result = self.dispatch(world, "GET" if method == "HEAD" else method, path, data, parse_qs(parsed.query))
                if fresh:
                    self.set_cookie(self.workspace_cookie, sid)
            self.respond(status, result)
        except ApiError as exc:
            self.pending_cookies = []
            self.respond(exc.status, {"error": exc.message, "code": exc.code})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            import traceback
            traceback.print_exc()
            self.pending_cookies = []
            self.respond(500, {"error": "Something went wrong. Try again.", "code": "server_error"})

    do_GET = do_HEAD = do_POST = do_PUT = do_PATCH = do_DELETE = handle_request


def build_server(host="127.0.0.1", port=3200, db_path="data/medisupply.sqlite3"):
    server = ThreadingHTTPServer((host, port), Handler)
    server.store = Store(db_path)
    digest = hashlib.sha256()
    for file in [ROOT / "server.py", ROOT / "store.py", ROOT / "orders.py", *sorted((ROOT / "static").rglob("*"))]:
        if file.is_file():
            digest.update(file.read_bytes())
    server.build_id = os.environ.get("RADIUS_SOURCE_SHA") or digest.hexdigest()[:40]
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MediSupply pharmacy ordering portal")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3200")))
    parser.add_argument("--database", default=os.environ.get("MEDISUPPLY_DATABASE", str(ROOT / "data" / "medisupply.sqlite3")))
    args = parser.parse_args()
    app = build_server(args.host, args.port, args.database)
    print(f"MediSupply listening at http://{args.host}:{app.server_port}", flush=True)
    try:
        app.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        app.server_close()
