"""Persistent, isolated workspaces and reproducible distribution data."""
from __future__ import annotations

import json
import os
import secrets
import sqlite3
import time
from contextlib import closing, contextmanager
from datetime import date, timedelta
from pathlib import Path

ACCOUNTS = {
    "buyer@greenfield.demo": {"id": "greenfield", "name": "Sarah Mitchell", "role": "pharmacy", "organization": "Greenfield Pharmacy", "initials": "SM"},
    "buyer@riverside.demo": {"id": "riverside", "name": "Alex Chen", "role": "pharmacy", "organization": "Riverside Pharmacy", "initials": "AC"},
    "admin@medisupply.demo": {"id": "admin", "name": "Jordan Ellis", "role": "admin", "organization": "MediSupply Distribution", "initials": "JE"},
}
PASSWORD = "MediSupply2026!"
BUSINESS_DATE = os.environ.get("MEDISUPPLY_DATE", "2026-11-16")


def seed() -> dict:
    today = date.fromisoformat(BUSINESS_DATE)
    # Prices and inventory describe fictional demonstration packs, not retail offers.
    rows = [
        ("amoxicillin", "Amoxicillin", "500 mg", "100 capsules", "Antibiotics", "Northstar Generics", 1250, 100, 30, 420, "AMX-2608", "Ambient"),
        ("metformin", "Metformin", "500 mg", "100 tablets", "Diabetes care", "Aster Pharmaceuticals", 840, 240, 40, 510, "MET-2609", "Ambient"),
        ("atorvastatin", "Atorvastatin", "20 mg", "90 tablets", "Cardiovascular", "Northstar Generics", 1825, 18, 30, 360, "ATV-2606", "Ambient"),
        ("lisinopril", "Lisinopril", "10 mg", "100 tablets", "Cardiovascular", "Aster Pharmaceuticals", 950, 150, 30, 390, "LIS-2607", "Ambient"),
        ("cetirizine", "Cetirizine", "10 mg", "30 tablets", "Allergy & respiratory", "Crestwell Health", 475, 72, 20, 270, "CET-2604", "Ambient"),
        ("omeprazole", "Omeprazole", "20 mg", "28 capsules", "Gastrointestinal", "Northstar Generics", 680, 85, 20, 300, "OMP-2605", "Ambient"),
        ("paracetamol", "Paracetamol", "500 mg", "100 tablets", "Pain relief", "Crestwell Health", 320, 320, 60, 570, "PAR-2610", "Ambient"),
        ("azithromycin", "Azithromycin", "250 mg", "6 tablets", "Antibiotics", "Aster Pharmaceuticals", 1475, 40, 20, -32, "AZI-2504", "Ambient"),
        ("insulin", "Insulin glargine", "100 units/mL", "5 × 3 mL pens", "Diabetes care", "Helix Biologics", 8920, 12, 20, 180, "INS-2609", "Cold chain · 2–8°C"),
        ("salbutamol", "Salbutamol", "100 mcg/dose", "200-dose inhaler", "Allergy & respiratory", "Crestwell Health", 1120, 0, 20, 240, "SAL-2603", "Ambient"),
        ("amlodipine", "Amlodipine", "5 mg", "90 tablets", "Cardiovascular", "Aster Pharmaceuticals", 725, 96, 25, 450, "AML-2608", "Ambient"),
        ("ibuprofen", "Ibuprofen", "400 mg", "84 tablets", "Pain relief", "Crestwell Health", 560, 160, 30, 30, "IBU-2601", "Ambient"),
    ]
    products = {}
    for i, row in enumerate(rows, 1):
        pid, name, strength, pack, category, manufacturer, price, stock, threshold, expires, lot, storage = row
        products[pid] = dict(id=pid, code=f"MED-{1000+i}", name=name, strength=strength, pack=pack,
                             category=category, manufacturer=manufacturer, price_cents=price, stock=stock,
                             reorder_level=threshold, expires_on=(today + timedelta(days=expires)).isoformat(), lot=lot, storage=storage)

    def order(number, status, days, items, owner="greenfield", po=""):
        lines = [{**products[pid], "quantity": qty, "line_total_cents": products[pid]["price_cents"] * qty} for pid, qty in items]
        total = sum(line["line_total_cents"] for line in lines)
        created = f"{today - timedelta(days=days)}T09:30:00Z"
        history = [{"status": "submitted", "at": created, "note": "Order received by MediSupply."}]
        stages = ["submitted", "processing", "shipped", "delivered"]
        if status in stages:
            for step in stages[1:stages.index(status) + 1]:
                history.append({"status": step, "at": f"{today - timedelta(days=max(0, days-1))}T14:10:00Z", "note": {"processing": "Warehouse picking started.", "shipped": "Handed to distribution carrier.", "delivered": "Delivery confirmed at pharmacy."}[step]})
        if status == "cancelled":
            history.append({"status": status, "at": created, "note": "Cancelled by pharmacy."})
        return dict(id=f"MS-{number}", status=status, owner=owner, pharmacy="Greenfield Pharmacy" if owner == "greenfield" else "Riverside Pharmacy", created_at=created,
                    purchase_order=po or f"GF-{number-800:04d}", notes="", lines=lines, subtotal_cents=total,
                    discount_cents=0, discount_code="", total_cents=total, history=history,
                    expected_delivery=(today + timedelta(days=1 if status == "shipped" else 2)).isoformat(),
                    tracking_reference=f"MSX{number}062" if status in {"shipped", "delivered"} else None,
                    ship_to="Greenfield Pharmacy, 184 Oak Street, Columbus, OH 43215" if owner == "greenfield" else "Riverside Pharmacy, 52 River Road, Columbus, OH 43215",
                    stock_reserved=status in {"submitted", "processing"})

    orders = [
        order(1048, "submitted", 0, [("metformin", 20), ("cetirizine", 12)]),
        order(1047, "processing", 1, [("amoxicillin", 10), ("omeprazole", 15)]),
        order(1046, "shipped", 2, [("atorvastatin", 8), ("lisinopril", 10)]),
        order(1045, "delivered", 5, [("paracetamol", 40), ("metformin", 30)]),
        order(1044, "delivered", 8, [("amoxicillin", 20), ("amlodipine", 10)]),
        order(1043, "cancelled", 10, [("cetirizine", 10)]),
        order(1042, "submitted", 1, [("lisinopril", 10)], "riverside", "RV-0242"),
    ]
    return {"business_date": BUSINESS_DATE, "user": None, "auth": None, "signed_in_at": 0,
            "products": products, "orders": orders, "cart": [], "discount_code": "", "next_order": 1049,
            "inventory_history": [], "submissions": {}}


class Store:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS workspaces (id TEXT PRIMARY KEY, payload TEXT NOT NULL, touched REAL NOT NULL)")
            db.commit()

    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.execute("PRAGMA busy_timeout=15000")
        return db

    @contextmanager
    def workspace(self, sid):
        db = self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload FROM workspaces WHERE id=? AND touched>?", (sid or "", time.time()-86400)).fetchone()
            fresh = row is None
            if fresh:
                sid, world = secrets.token_urlsafe(32), seed()
                db.execute("DELETE FROM workspaces WHERE touched<?", (time.time()-86400,))
                db.execute("DELETE FROM workspaces WHERE id IN (SELECT id FROM workspaces ORDER BY touched DESC LIMIT -1 OFFSET 2000)")
            else:
                world = json.loads(row[0])
            yield sid, world, fresh
            db.execute("INSERT OR REPLACE INTO workspaces(id,payload,touched) VALUES(?,?,?)", (sid, json.dumps(world, ensure_ascii=False), time.time()))
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()
