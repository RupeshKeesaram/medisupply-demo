# MediSupply requirements

This document defines expected behavior. It is the acceptance contract for all application versions. The scope is a demonstration of pharmacy procurement and warehouse operations, using fictional data only.

## R-01 — Identity and roles

1. A pharmacy user and an administrator can sign in with documented demo credentials. Wrong credentials return HTTP 401 and show a clear sign-in error.
2. The server determines the role from the authenticated account. A role submitted by the client grants no additional permissions.
3. Unauthenticated cart, order and inventory requests return 401. Public catalog and quote operations do not require sign-in.
4. Pharmacy users see only their pharmacy's orders. An identifier belonging to another pharmacy returns 404. Administrators can see all orders in their workspace.
5. Sign-out invalidates the authenticated session. Protected pages then return to the sign-in screen.
6. Each browser context has isolated demonstration data. Inventory and order updates persist on refresh and process restart. There is no global reset through the application.

## R-02 — Dashboard

1. Show the five most recent visible orders with order number, PO reference, placed date, item count, status and total.
2. Open orders means Submitted plus Processing. In transit means Shipped. Order value sums visible non-cancelled orders.
3. Stock alerts identify expired lots, out-of-stock products and low-stock products. Counts agree with the inventory view.
4. Each recent order links to its detail page. Catalog, orders and inventory are reachable from navigation.

## R-03 — Medication catalog

1. Search medication names and product codes case-insensitively, with whitespace trimmed.
2. Category, manufacturer and availability filters combine with AND. Empty filters show all products. An unmatched search shows an empty state and a way to clear filters.
3. Display name, strength, pack size, product code, manufacturer, category, USD pack price, available packs, lot identifier, expiry and storage condition where relevant.
4. Availability precedence is Expired, Out of stock, Low stock, then In stock. Low stock means positive stock at or below the reorder level; expired stock never counts as available regardless of quantity.
5. Availability is calculated against the workspace's displayed operations date. A lot remains valid on its expiry date, and is expired the following day.

## R-04 — Quantities and inventory validation

1. Every line requires a known `product_id` and an integer quantity from **1 through 10,000 packs**. Booleans, fractions, strings, null, zero, negatives and larger numbers return **400**.
2. The combined quantity for a product, including duplicate request lines and additions to the existing cart, must not exceed its available stock. Exactly the available quantity is valid; one more is invalid.
3. Stock validation applies to quotations, cart changes and final order submission. Stock is rechecked immediately before reservation.
4. A cart does not reserve stock. A submitted order reduces stock by its accepted quantities exactly once.
5. Validation failure changes no cart, stock, discounts, orders or counters. All lines of a submission are accepted atomically or none are accepted.
6. Quotation and order attempts involving an expired lot return **400**, regardless of available quantity. An expired product may remain visible for inventory review.

Examples at the default seed: Amoxicillin has 100 packs. 100 is valid; 101 and 120 are invalid. Azithromycin has 40 packs in an expired lot and cannot be ordered. Salbutamol has zero packs and cannot be ordered.

## R-05 — Pricing

1. Prices are per pack, represented as integer USD cents. A line total is unit price multiplied by quantity; subtotal is the sum of all line totals.
2. `CARE10`, matched without case sensitivity and ignoring surrounding whitespace, discounts the entire medication subtotal by **10%**.
3. Round the aggregate discount to the nearest cent, with halves rounded up, once per order. Never round each pack or line independently.
4. Apply one discount only. Applying the same code again must leave pricing unchanged. Changing a quantity recalculates the discount from the new subtotal.
5. Order total equals subtotal minus discount. Delivery is included and additional tax is not modeled. Total cannot be negative for valid orders.
6. An unsupported code returns 400 without changing the existing cart or its discount. Removing the code restores the undiscounted total.
7. Catalog, cart, quotation, confirmation and order history must agree. Submitted order pricing remains unchanged by subsequent inventory adjustments.

| Cart | Subtotal | CARE10 discount | Total |
| --- | ---: | ---: | ---: |
| 10 × Amoxicillin at $12.50 | $125.00 | $12.50 | $112.50 |
| 3 × Cetirizine at $4.75 | $14.25 | $1.43 | $12.82 |
| 2 × Amoxicillin + 3 × Cetirizine | $39.25 | $3.93 | $35.32 |

## R-06 — Order creation

1. Add products from the catalog, update pack quantities, remove individual lines, and retain the cart across page changes and refreshes.
2. An empty cart cannot be submitted. Require a nonblank PO reference of at most 60 characters. Delivery notes are optional, limited to 500 characters.
3. A successful submission returns 201, creates a unique `MS-` order number, stores its medication/lot/price snapshot, reserves stock, records Submitted history and clears the cart and discount.
4. Retrying the same submission identifier returns the original order with 200, without reserving additional stock or creating another order. Identifiers are scoped to the submitting account.
5. Show the resulting order and a success confirmation. A submission failure retains the editable cart and explains the problem.

## R-07 — Inventory administration

1. Pharmacy users can view inventory. **Only administrators** may change it, including through direct HTTP requests. A signed-in pharmacy user's stock update returns **403** and changes nothing.
2. Administrators may set stock to an integer from 0 through 100,000. Require an adjustment reason of 3–200 characters. Invalid adjustments return 400.
3. Save product, old quantity, new quantity, reason, actor and UTC timestamp in adjustment history.
4. Update inventory indicators and dashboard alerts immediately after a valid change. Stock changes do not change lot expiry or make expired inventory eligible for ordering.

## R-08 — Tracking and cancellation

1. Orders progress through **Submitted → Processing → Shipped → Delivered**. Only administrators may advance status. Skipping or reversing a stage returns 409 and changes nothing.
2. Preserve a chronological history with status, timestamp and explanation. Shipped and Delivered orders expose a demonstration tracking reference; no external shipment call occurs.
3. Pharmacy users can cancel their own Submitted or Processing orders; administrators can cancel eligible visible orders.
4. Cancellation of Shipped, Delivered or Cancelled orders returns **409**. Their status, history and inventory must remain unchanged.
5. Cancelling an eligible order releases its reserved stock once and records Cancelled history. Repeating cancellation never restores stock twice.
6. Filter order history by status and search by order ID or PO reference. Empty results have a clear recovery path.

## R-09 — HTTP and interface behavior

1. Malformed JSON, invalid fields and invalid business-rule inputs return 400 with `{ "error": "Human-readable message", "code": "machine_code" }`; never return a success response for a rejected operation.
2. Use 401 for missing/invalid authentication, 403 for insufficient privilege, 404 for unknown/inaccessible resources, and 409 for forbidden order-state transitions.
3. Reject oversized request bodies and cross-site state-changing requests. No stack traces or authentication tokens appear in responses.
4. `/health` and `/version` return successful JSON. Version identifies the built source. Pages support direct URLs, refresh, browser back and forward.
5. Use labeled fields, keyboard-operable controls, visible focus, table headings, readable status words, announced errors and responsive layout. Data tables may scroll horizontally within their own container on a phone; the whole page must not overflow.

## Scope limits

One demonstration distribution center, one lot per medication, fixed fictional prices, two pharmacy accounts and one administrator. No insurance billing, controlled-substance workflows, prescription verification, clinical decision support, patient data, payments, carrier integration, DSCSA claims or production compliance claims.
