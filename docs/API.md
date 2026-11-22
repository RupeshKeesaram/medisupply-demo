# HTTP API

All requests and responses use JSON. Currency is USD; amounts use integer cents. Supply `Content-Type: application/json` with request bodies. Errors use `{ "error": "message", "code": "reason" }`.

## Public resources

| Method | Route | Result |
| --- | --- | --- |
| GET | `/health` | `status`, `application`, source `commit` |
| GET | `/version` | Same version identity as health |
| GET | `/api/session` | Current `user` or null, and `business_date` |
| GET | `/api/catalog` | `products`, `total`, `categories`, `manufacturers`, `business_date` |
| POST | `/api/quote` | Validated line items and pricing; no stock reservation |
| POST | `/api/login` | Authenticated `user`; session cookies |
| POST | `/api/logout` | Clear authentication and cart; `ok: true` |

Catalog query parameters: `q`, `category`, `manufacturer`, `availability`. Availability is `in_stock`, `low_stock`, `out_of_stock` or `expired`. See the catalog for exact IDs and available quantities. Examples: `amoxicillin`, `metformin`, `cetirizine`, `azithromycin`.

Quotation request:

```json
{
  "items": [
    { "product_id": "amoxicillin", "quantity": 10 }
  ],
  "discount_code": "CARE10"
}
```

Successful quote response includes `lines`, `subtotal_cents: 12500`, `discount_cents: 1250`, `total_cents: 11250`, `shipping_cents: 0`, `currency: "USD"`, `discount_code: "CARE10"`. Each line includes product metadata, `quantity` and `line_total_cents`. Unknown product IDs return 404. Invalid quantities, insufficient stock, expired lots and unknown codes return 400, with no mutation.

Sign-in body: `{ "email": "buyer@greenfield.demo", "password": "MediSupply2026!" }`. Keep both returned HttpOnly cookies in the client cookie jar. Account role is resolved on the server. See README for administrator and second-pharmacy accounts. No bearer token or client-specified role is supported.

## Authenticated resources

| Method | Route | Body / result |
| --- | --- | --- |
| GET | `/api/dashboard` | Visible recent `orders`, inventory `alerts`, `metrics`, operations date |
| GET | `/api/cart` | Current cart in quotation response shape |
| PUT | `/api/cart` | Replace `items`, optional `discount_code`; returns validated cart |
| GET | `/api/orders` | Visible `orders`, newest first |
| GET | `/api/orders/MS-1046` | One visible `order` |
| POST | `/api/orders` | Create an order; 201, or 200 on idempotent replay |
| POST | `/api/orders/cancel` | `{ "order_id": "MS-1048" }`; returns updated `order` |
| PATCH | `/api/orders/status` | Administrator: `{ "order_id": "MS-1048", "status": "processing" }` |
| GET | `/api/inventory` | `products` and last 20 stock adjustments as `history` |
| PATCH | `/api/inventory` | Administrator: set absolute stock quantity with a reason |

Create order:

```json
{
  "items": [{ "product_id": "amoxicillin", "quantity": 10 }],
  "discount_code": "CARE10",
  "purchase_order": "GF-NOV-014",
  "notes": "Receiving desk open 9am–5pm",
  "idempotency_key": "unique-request-reference-001"
}
```

Omitting `items` and `discount_code` uses the saved cart. The cart is revalidated in the same SQLite transaction that reserves stock and persists the order. The idempotency identifier is required, 8–100 characters, and scoped to the authenticated account. A retry with that identifier returns the first accepted order without changes. A failed request does not consume its identifier.

Inventory adjustment:

```json
{
  "product_id": "atorvastatin",
  "stock": 80,
  "reason": "Warehouse receipt confirmed"
}
```

Returns `product` and `adjustment`, including `before`, `after`, `by`, `at`, and `reason`. A pharmacy user receives 403. Unauthenticated requests receive 401. Invalid stock/reason receives 400.

Cancellation is accepted only for Submitted or Processing orders. Other states return 409. Status advancement follows the next stage only; skipping a stage returns 409. Access to another pharmacy's order returns 404.

## Data isolation

Workspaces are assigned using an opaque browser cookie. Different browser contexts receive independent stock, carts and orders. Signing in as a different account in the same browser preserves the workspace but clears the cart; the account's order visibility still applies. Cookies are port-specific for local parallel instances. Set `MEDISUPPLY_SECURE_COOKIES=1` when serving behind HTTPS.
