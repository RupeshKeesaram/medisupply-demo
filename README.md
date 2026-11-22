# MediSupply — Pharmacy Ordering Portal

A compact pharmaceutical distribution application: pharmacy staff order medication packs, follow shipments and review stock; administrators maintain inventory and advance fulfillment. All accounts, organizations, prices and stock are fictional. No patient records, prescriptions, payments or external deliveries are involved.

## Run

Python **3.12+**, with no third-party runtime dependencies:

```bash
python server.py --port 3200
```

Open **http://localhost:3200**. Choose a role on the sign-in screen; the demo credentials are filled in.

| Role | Email | Password |
| --- | --- | --- |
| Pharmacy purchaser | `buyer@greenfield.demo` | `MediSupply2026!` |
| Distribution administrator | `admin@medisupply.demo` | `MediSupply2026!` |
| Second pharmacy | `buyer@riverside.demo` | `MediSupply2026!` |

The role selector fills an account; the server derives permissions from that account. A new browser context receives a separate workspace. Reloads and server restarts retain that workspace in SQLite for 24 hours of inactivity. Signing out clears authentication and the cart, retaining inventory and order history. Sign-in sessions last eight hours.

## Business rules

The complete acceptance contract is [REQUIREMENTS.md](REQUIREMENTS.md). Core rules:

- Quantities are **positive whole packs**, from 1 through 10,000, and may not exceed current stock. Duplicate lines count toward the same stock limit.
- Expired lots cannot be quoted, added to a cart or ordered. Expiry is compared with the displayed operations date, including on order submission.
- **CARE10** applies exactly **10%** to the medication subtotal, once per order. Round the aggregate discount to the nearest cent, half up. Delivery is included; no additional tax is modeled. Ten Amoxicillin packs at $12.50 cost **$125.00**, less **$12.50**, for **$112.50**.
- Only administrators may adjust stock, and every adjustment needs a reason. Pharmacy accounts can view inventory. API access follows the same rule.
- Only **Submitted** and **Processing** orders may be cancelled. Cancellation restores reserved stock once. Shipped, Delivered and Cancelled orders reject cancellation with HTTP **409**.
- Invalid quantities return HTTP **400**, with no mutation. A repeated submission with the same request identifier creates one order.

## Work areas

| Page | Purpose |
| --- | --- |
| `/login` | Pharmacy or administrator sign-in |
| `/dashboard` | Recent orders, pending shipments and stock alerts |
| `/catalog` | Search by name or code; filter category, manufacturer and availability |
| `/cart` | Update quantities, apply a discount, enter a PO reference and submit |
| `/inventory` | Lot expiry, stock levels and administrator stock adjustments |
| `/orders` | Order history, status filters and tracking |
| `/orders/MS-1046` | An example shipment with fulfillment history |

## API

See [docs/API.md](docs/API.md) for routes, request shapes and status codes. `GET /api/catalog` and `POST /api/quote` are public, read-only catalog/quotation operations. Mutations to orders, carts and inventory require a signed-in session. They are suitable for browser-driven workflows; the public quote endpoint can be verified independently with ordinary HTTP requests.

```bash
curl -X POST http://localhost:3200/api/quote -H "Content-Type: application/json" -d '{"items":[{"product_id":"amoxicillin","quantity":10}],"discount_code":"CARE10"}'
```

The response expresses money as integer cents (`subtotal_cents`, `discount_cents`, `total_cents`). The same server calculation supplies the UI, cart and order receipt. `/health` and `/version` return JSON; the version includes `RADIUS_SOURCE_SHA` when provided, otherwise a source digest.

## Repeatable data

The default operations date is **2026-11-16**. Seeded lot expiry dates, stock, order references and statuses stay consistent across fresh browser contexts. `MEDISUPPLY_DATE=YYYY-MM-DD` changes the operations date of newly created workspaces. Existing workspaces keep their original date. This date is for business-rule evaluation; actual new-order and audit timestamps use UTC wall time.

Local data is stored in `data/medisupply.sqlite3`. Set `--database PATH` or `MEDISUPPLY_DATABASE` for a separate instance. Use a fresh browser context to start a clean workspace; there is no global reset endpoint. Separate ports use separate cookies. SQLite transactions serialize inventory reservations, cancellations and adjustments.

## Containers and Radius

```bash
docker compose up --build -d
```

The local Compose file serves port 3200 and retains SQLite in a named volume. `docker compose down` stops it and retains the volume.

`radius.test.yaml` and `compose.radius.yaml` follow Radius Test's repository contract: one non-root service, a JSON health endpoint, no fixed host ports, and a writable database under `/tmp`. Connect the repository's `main` branch in Radius. Configure a pharmacy test account to explore signed-in journeys; the account should use the credentials above. No changes to Radius are required.

## Verification

```bash
python -m unittest discover -s tests -v
node --check static/app.js
```

The HTTP acceptance suite uses temporary databases and real HTTP requests. It verifies requirements, persistence, account isolation and atomic mutations. The frontend uses semantic HTML, labeled forms, native controls, local fonts and no external runtime resources.

## Layout

- `server.py`: routes, sessions and HTTP boundary.
- `orders.py`: quotation, reservations and order lifecycle.
- `store.py`: SQLite workspace storage and fictional seed records.
- `static/`: browser application, styles and self-hosted IBM Plex Sans (OFL license included).
- `REQUIREMENTS.md`: expected behavior, independent of implementation.
- `docs/API.md`: HTTP contract.

This application models procurement workflows only. It does not claim regulatory compliance, medical validity or affiliation with a pharmaceutical distributor.
