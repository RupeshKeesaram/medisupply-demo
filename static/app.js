"use strict";

const app = document.querySelector("#app");
const state = { user: null, businessDate: "", cart: null, page: null, loading: false, loginRole: "pharmacy", generation: 0, checkoutDraft: { purchase_order: "", notes: "" } };
const money = cents => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(cents / 100);
const dateLabel = value => value ? new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" }).format(new Date(value.length === 10 ? value + "T12:00:00Z" : value)) : "To be confirmed";
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const titleCase = value => ({ in_stock: "In stock", low_stock: "Low stock", out_of_stock: "Out of stock", expired: "Expired", submitted: "Submitted", processing: "Processing", shipped: "Shipped", delivered: "Delivered", cancelled: "Cancelled" }[value] || value);
const paths = {
  dashboard: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  catalog: '<path d="M12 5c-3-2-6-2-9-1v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1v15"/>',
  orders: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2h6v2M9 9h6M9 13h6M9 17h3"/>',
  inventory: '<path d="m3 7 9-4 9 4-9 4-9-4Zm0 0v10l9 4 9-4V7M12 11v10M7.5 5 17 9"/>',
  truck: '<path d="M3 5h12v12H3V5Zm12 5h3l3 4v3h-6"/><circle cx="7" cy="18" r="2"/><circle cx="18" cy="18" r="2"/>',
  cart: '<path d="M3 3h2l3 13h11l2-9H6M9 20h.01M18 20h.01"/><circle cx="9" cy="20" r="1"/><circle cx="18" cy="20" r="1"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
  arrow: '<path d="M5 12h14m-6-6 6 6-6 6"/>',
  chevron: '<path d="m9 5 7 7-7 7"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  alert: '<path d="m12 3 10 18H2L12 3Zm0 6v5m0 3h.01"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  logout: '<path d="M9 4H4v16h5m6-13 5 5-5 5M9 12h11"/>',
  leaf: '<path d="M20 4c-8-2-15 1-15 8 0 4 3 6 6 6 7 0 9-7 9-14ZM4 21l11-11"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  box: '<path d="M5 7h14v14H5V7Zm-1 0h16V3H4v4Zm6 5h4"/>',
  lock: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2"/>',
  edit: '<path d="m15 4 5 5M4 20l5-1L21 7a2 2 0 0 0-5-5L4 14v6Z"/>',
};
const icon = (name, cls = "") => `<svg class="icon ${cls}" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.box}</svg>`;
const badge = status => `<span class="badge badge-${esc(status)}"><span class="status-dot"></span>${esc(titleCase(status))}</span>`;

async function api(path, options = {}) {
  const response = await fetch(path, { credentials: "same-origin", ...options, headers: { "Content-Type": "application/json", ...options.headers } });
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error || "The request could not be completed.");
    error.status = response.status;
    error.code = data.code;
    if (response.status === 401 && !["/api/login", "/api/session"].includes(path)) {
      state.user = null;
      state.cart = null;
      navigate("/login");
    }
    throw error;
  }
  return data;
}
const send = (path, method, body) => api(path, { method, body: JSON.stringify(body) });

function notify(message, type = "success") {
  const area = document.querySelector("#notifications");
  area.innerHTML = `<div class="toast toast-${type}">${icon(type === "error" ? "alert" : "check")}<span>${esc(message)}</span><button class="icon-button" aria-label="Dismiss notification" data-action="dismiss-toast">${icon("close")}</button></div>`;
  clearTimeout(notify.timer);
  notify.timer = setTimeout(() => { area.innerHTML = ""; }, 6500);
}

function navigate(path, replace = false) {
  if (location.pathname + location.search !== path) history[replace ? "replaceState" : "pushState"]({}, "", path);
  return render();
}

function logo() { return '<img src="/static/mark.svg" width="34" height="34" alt=""><span>MediSupply<span class="brand-caption">Pharmacy ordering</span></span>'; }

function shell(content) {
  const path = location.pathname;
  const nav = [["/dashboard", "dashboard", "Overview"], ["/catalog", "catalog", "Medication catalog"], ["/orders", "orders", "Orders & tracking"], ["/inventory", "inventory", "Inventory"]];
  const total = state.cart?.lines.reduce((n, line) => n + line.quantity, 0) || 0;
  app.innerHTML = `<div class="app-shell">
    <aside class="sidebar" aria-label="Main navigation">
      <a class="brand" href="/dashboard">${logo()}</a>
      <div class="workspace-label">YOUR WORKSPACE</div>
      <nav>${nav.map(([href, name, label]) => `<a href="${href}" class="nav-link ${path.startsWith(href) ? "active" : ""}" ${path.startsWith(href) ? 'aria-current="page"' : ""}>${icon(name)}<span>${label}</span>${path.startsWith(href) ? '<span class="nav-active-mark"></span>' : ""}</a>`).join("")}</nav>
      <div class="sidebar-bottom"><div class="account-block"><span class="avatar">${esc(state.user.initials)}</span><div><strong>${esc(state.user.name)}</strong><span>${state.user.role === "admin" ? "Distribution administrator" : "Pharmacy purchaser"}</span></div></div><button class="signout" data-action="logout">${icon("logout")} Sign out</button></div>
    </aside>
    <div class="main-shell">
      <header class="topbar"><div class="organization">${icon(state.user.role === "admin" ? "inventory" : "leaf")}<div><strong>${esc(state.user.organization)}</strong><span>${state.user.role === "admin" ? "Distribution workspace" : "Pharmacy account · GF-00842"}</span></div></div><div class="topbar-actions"><span class="demo-label">Demo workspace</span><a class="cart-link" href="/cart">${icon("cart")}<span>Order cart</span><span class="cart-count">${total}</span></a></div></header>
      <main id="main" class="main-content" tabindex="-1">${content}</main>
      <footer class="page-footer"><span>MediSupply · Fictional data for demonstration</span><span>Operations date: ${dateLabel(state.businessDate)}</span></footer>
    </div>
  </div>`;
  app.querySelectorAll(".table-scroll").forEach(region => {
    region.tabIndex = 0;
    region.setAttribute("role", "region");
    region.setAttribute("aria-label", region.querySelector("caption")?.textContent || "Data table");
  });
}

function pageHead(title, subtitle, action = "") {
  return `<div class="page-heading"><div><h1>${title}</h1><p>${subtitle}</p></div>${action}</div>`;
}
function empty(title, description, action = "") {
  return `<div class="empty-state">${icon("box")}<h2>${title}</h2><p>${description}</p>${action}</div>`;
}
function errorPanel(error) {
  return `<div class="error-panel" role="alert">${icon("alert")}<div><h2>We couldn’t load this page</h2><p>${esc(error.message)}</p><button class="button secondary" data-action="retry">Try again</button>${location.pathname === "/cart" ? '<button class="text-button" data-action="clear-cart">Clear cart</button>' : ""}</div></div>`;
}

function renderLogin() {
  const admin = state.loginRole === "admin";
  app.innerHTML = `<main id="main" class="login-layout"><section class="login-story"><a class="brand" href="/login">${logo()}</a><div class="login-story-content"><h1>Every order.<br>Every pharmacy.<br><span>Within reach.</span></h1><p>A clearer way to keep your pharmacy supplied. Order essentials, manage stock, and follow every delivery.</p><div class="supply-flow"><div>${icon("catalog")}<span>Source</span></div><span class="flow-line"></span><div>${icon("inventory")}<span>Supply</span></div><span class="flow-line"></span><div>${icon("truck")}<span>Deliver</span></div></div><div class="story-note">Built around the work behind better care.</div></div><div class="login-footer">MediSupply · Pharmacy Ordering Portal</div></section>
    <section class="login-panel"><div class="login-form-wrap"><h2>Welcome back</h2><p class="muted">Sign in to your ordering workspace.</p><span class="demo-label login-demo-label">Demo workspace</span><div class="role-switch" role="group" aria-label="Account role"><button type="button" data-action="login-role" data-role="pharmacy" aria-pressed="${!admin}" class="${!admin ? "selected" : ""}">Pharmacy user</button><button type="button" data-action="login-role" data-role="admin" aria-pressed="${admin}" class="${admin ? "selected" : ""}">Administrator</button></div>
    <form id="login-form"><div class="form-field"><label for="email">Email address</label><input type="email" id="email" name="email" autocomplete="username" required value="${admin ? "admin@medisupply.demo" : "buyer@greenfield.demo"}"></div><div class="form-field"><label for="password">Password</label><input type="password" id="password" name="password" autocomplete="current-password" required value="MediSupply2026!"></div><div id="login-error" class="form-error" role="alert"></div><button class="button primary full" type="submit">Sign in ${icon("arrow")}</button></form><div class="demo-credentials">${icon("lock")}<div><strong>Ready to explore</strong><p>Demo credentials are filled in for you. Choose a role above, then sign in.</p><details><summary>View demo password</summary><code>MediSupply2026!</code></details></div></div><p class="login-disclaimer">Fictional products, prices and organizations.<br>No patient data or real transactions.</p></div></section></main>`;
}

function ordersTable(orders, compact = false) {
  if (!orders.length) return empty("No orders found", "Your submitted orders will appear here.", '<a class="button primary" href="/catalog">Browse medications</a>');
  return `<div class="table-scroll"><table><caption class="sr-only">${compact ? "Recent orders" : "Pharmacy orders"}</caption><thead><tr><th>Order / reference</th><th>Placed</th>${state.user.role === "admin" ? "<th>Pharmacy</th>" : ""}<th>Items</th><th>Status</th><th class="numeric">Total</th><th><span class="sr-only">Details</span></th></tr></thead><tbody>${orders.map(o => `<tr><td><a class="order-id" href="/orders/${esc(o.id)}">${esc(o.id)}</a><span class="cell-secondary">${esc(o.purchase_order)}</span></td><td>${dateLabel(o.created_at)}</td>${state.user.role === "admin" ? `<td>${esc(o.pharmacy)}</td>` : ""}<td>${o.lines.length} ${o.lines.length === 1 ? "line" : "lines"}</td><td>${badge(o.status)}</td><td class="numeric strong">${money(o.total_cents)}</td><td><a class="table-arrow" href="/orders/${esc(o.id)}" aria-label="View order ${esc(o.id)}">${icon("chevron")}</a></td></tr>`).join("")}</tbody></table></div>`;
}

function dashboard(data) {
  const m = data.metrics;
  return `${pageHead(`Your supply, at a glance.`, `Welcome back, ${esc(state.user.name.split(" ")[0])}. Here’s what needs your attention.`, '<a class="button primary" href="/catalog">' + icon("plus") + ' Create an order</a>')}
    <div class="overview-strip"><div class="overview-stat">${icon("orders")}<div><span>Open orders</span><strong>${m.open_orders}</strong><small>Awaiting fulfillment</small></div></div><div class="overview-stat">${icon("truck")}<div><span>In transit</span><strong>${m.in_transit}</strong><small>On the way to your pharmacy</small></div></div><div class="overview-stat">${icon("alert")}<div><span>Inventory alerts</span><strong>${m.inventory_alerts}</strong><small>Lots to review</small></div></div><div class="overview-stat">${icon("inventory")}<div><span>Order value</span><strong>${money(m.order_value_cents)}</strong><small>All non-cancelled orders</small></div></div></div>
    <div class="dashboard-columns"><section class="panel orders-panel"><div class="section-heading"><div><h2>Recent orders</h2><p>From your pharmacy to our warehouse.</p></div><a class="text-link" href="/orders">View all ${icon("arrow")}</a></div>${ordersTable(data.orders, true)}</section><section class="panel attention-panel"><div class="section-heading"><div><h2>Needs attention</h2><p>Keep the essentials in reach.</p></div><span class="small-count">${data.alerts.length}</span></div><div class="attention-list">${data.alerts.map(p => `<a href="/inventory?availability=${p.availability}" class="attention-item"><span class="alert-icon ${p.availability === "expired" ? "critical" : ""}">${icon(p.availability === "expired" ? "clock" : "inventory")}</span><div><strong>${esc(p.name)} <span>${esc(p.strength)}</span></strong><small>${p.availability === "expired" ? `Lot ${esc(p.lot)} · expired ${dateLabel(p.expires_on)}` : `${p.stock} packs available · reorder at ${p.reorder_level}`}</small>${badge(p.availability)}</div>${icon("chevron")}</a>`).join("") || '<p class="muted">All inventory levels are healthy.</p>'}</div><a class="panel-bottom-link" href="/inventory">Review inventory ${icon("arrow")}</a></section></div>
    <section class="replenish-banner"><div class="replenish-icon">${icon("catalog")}</div><div><h2>A well-stocked pharmacy starts here.</h2><p>Explore essential medications with pack pricing and lot availability in one view.</p></div><a class="button secondary" href="/catalog">Browse catalog ${icon("arrow")}</a></section>`;
}

function filterSelect(name, label, values, selected, allLabel) {
  return `<div class="filter-field"><label for="filter-${name}">${label}</label><select id="filter-${name}" name="${name}"><option value="">${allLabel}</option>${values.map(v => `<option value="${esc(v)}" ${selected === v ? "selected" : ""}>${esc(titleCase(v))}</option>`).join("")}</select></div>`;
}

function catalog(data) {
  const query = new URLSearchParams(location.search);
  return `${pageHead("Medication catalog", "The essentials for your pharmacy. Prices are per pack, in USD.", '<a class="button secondary" href="/cart">Review order cart ' + icon("arrow") + '</a>')}
    <section class="panel"><form id="catalog-filters" class="filters"><div class="filter-field search-field"><label for="filter-q">Search medications</label><div class="input-icon">${icon("search")}<input type="search" id="filter-q" name="q" placeholder="Medication name or product code" value="${esc(query.get("q") || "")}"></div></div>${filterSelect("category", "Category", data.categories, query.get("category"), "All categories")}${filterSelect("manufacturer", "Manufacturer", data.manufacturers, query.get("manufacturer"), "All manufacturers")}${filterSelect("availability", "Availability", ["in_stock", "low_stock", "out_of_stock", "expired"], query.get("availability"), "Any availability")}<button class="button secondary filter-button" type="submit">Search</button></form>
    <div class="results-header"><span><strong>${data.total}</strong> medications${query.size ? " matching your filters" : " in the catalog"}</span>${query.size ? '<a class="text-link" href="/catalog">Clear filters</a>' : '<span>Live availability · packs</span>'}</div>
    ${data.products.length ? `<div class="table-scroll"><table class="catalog-table"><caption class="sr-only">Medication catalog with prices, stock, lot expiry and ordering controls</caption><thead><tr><th>Medication</th><th>Manufacturer</th><th class="numeric">Pack price</th><th>Availability</th><th>Lot / expiry</th><th>Order quantity</th></tr></thead><tbody>${data.products.map(p => `<tr><td><div class="medication-cell"><span class="medication-icon">${icon("box")}</span><div><strong>${esc(p.name)} <span class="strength">${esc(p.strength)}</span></strong><span class="cell-secondary">${esc(p.pack)} · ${esc(p.code)}</span><span class="category-label">${esc(p.category)}</span></div></div></td><td>${esc(p.manufacturer)}${p.storage !== "Ambient" ? `<span class="cell-secondary cold-chain">${esc(p.storage)}</span>` : ""}</td><td class="numeric strong">${money(p.price_cents)}</td><td>${badge(p.availability)}<span class="cell-secondary">${p.stock} packs ${p.availability === "expired" ? "on hand" : "available"}</span></td><td><span class="lot-code">${esc(p.lot)}</span><span class="cell-secondary ${p.availability === "expired" ? "danger-text" : ""}">${dateLabel(p.expires_on)}</span></td><td><form class="add-form" data-product="${esc(p.id)}"><label class="sr-only" for="qty-${esc(p.id)}">Quantity for ${esc(p.name)}</label><input id="qty-${esc(p.id)}" type="number" name="quantity" min="1" step="1" value="1" required><button class="button add-button" type="submit" aria-label="Add ${esc(p.name)} to cart" ${p.stock === 0 ? "disabled" : ""}>${icon("plus")} Add</button></form></td></tr>`).join("")}</tbody></table></div>` : empty("No medications match", "Try another name, product code, or a different filter.", '<a class="button secondary" href="/catalog">Clear filters</a>')}</section><div class="catalog-note">${icon("lock")} Orders are validated against available stock and lot expiry at submission.</div>`;
}

function totals(cart) {
  return `<dl class="totals"><div><dt>Subtotal</dt><dd>${money(cart.subtotal_cents)}</dd></div><div class="discount-row"><dt>Discount${cart.discount_code ? ` · ${esc(cart.discount_code)}` : ""}</dt><dd>−${money(cart.discount_cents)}</dd></div><div><dt>Standard delivery</dt><dd>Included</dd></div><div class="grand-total"><dt>Order total</dt><dd>${money(cart.total_cents)}</dd></div></dl>`;
}

function cartPage(cart) {
  return `${pageHead("Your order cart", "Review quantities and pricing before sending your order.", '<a class="text-link" href="/catalog">Continue shopping ' + icon("arrow") + '</a>')}${!cart.lines.length ? `<section class="panel">${empty("Ready for your next order", "Add medications from the catalog to start a pharmacy order.", '<a class="button primary" href="/catalog">Browse medications</a>')}</section>` : `<div class="cart-layout"><div><section class="panel"><div class="section-heading"><h2>Order items <span class="muted">(${cart.lines.length})</span></h2><span class="muted">All quantities in packs</span></div><div class="cart-lines">${cart.lines.map(p => `<div class="cart-line"><span class="medication-icon">${icon("box")}</span><div class="cart-line-description"><h3>${esc(p.name)} <span>${esc(p.strength)}</span></h3><p>${esc(p.pack)} · ${esc(p.code)}</p><span class="muted">${money(p.price_cents)} per pack · ${p.stock} available</span></div><div class="cart-line-edit"><form class="quantity-form" data-product="${esc(p.id)}"><label for="cart-qty-${esc(p.id)}">Packs</label><div><input id="cart-qty-${esc(p.id)}" name="quantity" type="number" min="1" step="1" required value="${p.quantity}"><button class="text-button" type="submit">Update</button></div></form><button class="text-button muted" data-action="remove-line" data-product="${esc(p.id)}">Remove<span class="sr-only"> ${esc(p.name)}</span></button></div><strong class="line-price">${money(p.line_total_cents)}</strong></div>`).join("")}</div></section><section class="panel delivery-panel"><h2>Deliver to</h2><div class="delivery-address">${icon("leaf")}<div><strong>${esc(state.user.organization)}</strong><p>${state.user.id === "riverside" ? "52 River Road" : "184 Oak Street"}<br>Columbus, OH 43215</p></div></div><p class="muted">The warehouse will confirm delivery timing after your order is submitted.</p></section></div><aside class="panel order-summary"><h2>Order summary</h2><p class="muted">${cart.lines.reduce((n, l) => n + l.quantity, 0)} packs across ${cart.lines.length} medications</p>${totals(cart)}<form id="discount-form"><label for="discount-code">Discount code</label><div class="inline-input"><input id="discount-code" name="code" placeholder="Enter code" value="${esc(cart.discount_code)}"><button class="button secondary" type="submit">Apply</button></div><p class="field-hint">Use CARE10 for 10% off the medication subtotal. One discount per order.</p>${cart.discount_code ? '<button class="text-button" type="button" data-action="remove-discount">Remove discount</button>' : ""}</form><form id="checkout-form"><div class="form-field"><label for="purchase-order">Purchase order reference <span aria-hidden="true">*</span></label><input id="purchase-order" name="purchase_order" placeholder="e.g. GF-NOV-014" maxlength="60" required value="${esc(state.checkoutDraft.purchase_order)}"></div><div class="form-field"><label for="delivery-notes">Delivery notes <span class="muted">(optional)</span></label><textarea id="delivery-notes" name="notes" rows="2" maxlength="500" placeholder="Receiving hours or delivery instructions">${esc(state.checkoutDraft.notes)}</textarea></div><div id="checkout-error" class="form-error" role="alert"></div><button type="submit" class="button primary full">Submit order ${icon("arrow")}</button><p class="field-hint center">Stock is reserved when your order is accepted.</p></form></aside></div>`}`;
}

function ordersPage(data) {
  const query = new URLSearchParams(location.search);
  const status = query.get("status") || "";
  const q = (query.get("q") || "").toLowerCase();
  const orders = data.orders.filter(o => (!status || o.status === status) && (!q || (o.id + " " + o.purchase_order).toLowerCase().includes(q)));
  const statuses = ["", "submitted", "processing", "shipped", "delivered", "cancelled"];
  return `${pageHead("Orders & tracking", "Every order, from submission to your pharmacy door.", '<a class="button primary" href="/catalog">' + icon("plus") + ' Create an order</a>')}<section class="panel"><nav class="status-tabs" aria-label="Filter orders by status">${statuses.map(s => `<a href="/orders${s ? "?status=" + s : ""}" class="${s === status ? "selected" : ""}" ${s === status ? 'aria-current="page"' : ""}>${s ? titleCase(s) : "All orders"}<span>${data.orders.filter(o => !s || o.status === s).length}</span></a>`).join("")}</nav><form id="order-filters" class="order-search"><div class="input-icon">${icon("search")}<label class="sr-only" for="order-search">Search order or reference</label><input id="order-search" name="q" placeholder="Search order number or PO reference" value="${esc(query.get("q") || "")}"></div><input type="hidden" name="status" value="${esc(status)}"><button class="button secondary" type="submit">Search orders</button></form>${ordersTable(orders)}</section>`;
}

function orderDetail(order) {
  const stages = ["submitted", "processing", "shipped", "delivered"];
  const active = stages.indexOf(order.status);
  const next = stages[active + 1];
  return `<a class="back-link" href="/orders">${icon("arrow", "back-arrow")} Back to orders</a>${pageHead(`Order ${esc(order.id)}`, `PO reference ${esc(order.purchase_order)} · Placed ${dateLabel(order.created_at)}`, badge(order.status))}<div class="order-detail-layout"><div><section class="panel tracking-panel"><div class="section-heading"><h2>Order progress</h2>${order.tracking_reference ? `<span class="muted">Tracking ${esc(order.tracking_reference)}</span>` : ""}</div>${order.status === "cancelled" ? '<div class="cancelled-note">' + icon("close") + '<p>This order has been cancelled. Its history is retained below.</p></div>' : `<ol class="tracking-steps">${stages.map((s, i) => `<li class="${i <= active ? "reached" : ""} ${i === active ? "current" : ""}"><span class="step-mark">${i < active ? icon("check") : icon(["orders", "inventory", "truck", "check"][i])}</span><strong>${titleCase(s)}</strong><small>${i === active ? "Current status" : i < active ? "Complete" : "Upcoming"}</small></li>`).join("")}</ol>`}<div class="delivery-estimate">${icon("truck")}<span>${order.status === "delivered" ? "Delivered to your pharmacy" : order.status === "cancelled" ? "Delivery no longer scheduled" : `Expected delivery: ${dateLabel(order.expected_delivery)}`}</span></div></section><section class="panel"><div class="section-heading"><h2>Ordered medications</h2><span class="muted">${order.lines.length} lines</span></div><div class="table-scroll"><table><caption class="sr-only">Order line items</caption><thead><tr><th>Medication</th><th class="numeric">Packs</th><th class="numeric">Pack price</th><th class="numeric">Line total</th></tr></thead><tbody>${order.lines.map(p => `<tr><td><strong>${esc(p.name)} ${esc(p.strength)}</strong><span class="cell-secondary">${esc(p.pack)} · Lot ${esc(p.lot)}</span></td><td class="numeric">${p.quantity}</td><td class="numeric">${money(p.price_cents)}</td><td class="numeric strong">${money(p.line_total_cents)}</td></tr>`).join("")}</tbody></table></div><div class="order-totals">${totals(order)}</div></section><section class="panel history-panel"><h2>Order history</h2><ol class="history-list">${[...order.history].reverse().map(e => `<li><span class="history-dot"></span><div><strong>${titleCase(e.status)}</strong><p>${esc(e.note)}</p></div><time datetime="${esc(e.at)}">${dateLabel(e.at)}</time></li>`).join("")}</ol></section></div><aside><section class="panel delivery-panel"><h2>Delivery details</h2><div class="delivery-address">${icon("leaf")}<div><strong>${esc(order.pharmacy)}</strong><p>${esc(order.ship_to)}</p></div></div>${order.notes ? `<div class="delivery-notes"><strong>Delivery notes</strong><p>${esc(order.notes)}</p></div>` : ""}</section><section class="panel actions-panel"><h2>Manage this order</h2><p class="muted">Submitted and processing orders may be cancelled. Shipped orders cannot be cancelled.</p>${!["cancelled", "delivered"].includes(order.status) ? `<button class="button danger full" data-action="cancel-order" data-order="${esc(order.id)}">Cancel order</button>` : `<p class="field-hint">This order is ${esc(order.status)}.</p>`}${state.user.role === "admin" && active >= 0 && next ? `<button class="button primary full" data-action="advance-order" data-order="${esc(order.id)}" data-status="${next}">Mark as ${next}</button>` : ""}</section></aside></div>`;
}

function inventoryPage(data) {
  const query = new URLSearchParams(location.search);
  const filter = query.get("availability") || "";
  const search = (query.get("q") || "").toLowerCase();
  const rows = data.products.filter(p => (!filter || p.availability === filter) && (!search || (p.name + " " + p.code + " " + p.lot).toLowerCase().includes(search)));
  return `${pageHead("Inventory", "A clear view of every pack, every lot, and what needs replenishing.", `<span class="role-indicator">${icon(state.user.role === "admin" ? "edit" : "lock")}${state.user.role === "admin" ? "Stock adjustment access" : "View-only access"}</span>`)}<div class="inventory-summary"><a href="/inventory" class="inventory-summary-item ${!filter ? "selected" : ""}"><span>All medications</span><strong>${data.products.length}</strong></a>${["low_stock", "out_of_stock", "expired"].map(s => `<a href="/inventory?availability=${s}" class="inventory-summary-item ${filter === s ? "selected" : ""}"><span>${titleCase(s)}</span><strong>${data.products.filter(p => p.availability === s).length}</strong></a>`).join("")}</div><section class="panel"><form id="inventory-filters" class="inventory-filters"><div class="input-icon">${icon("search")}<label class="sr-only" for="inventory-search">Search inventory</label><input type="search" id="inventory-search" name="q" value="${esc(query.get("q") || "")}" placeholder="Search medication, code or lot"></div>${filterSelect("availability", "Availability", ["in_stock", "low_stock", "out_of_stock", "expired"], filter, "All inventory")}<button type="submit" class="button secondary">Search inventory</button></form>${rows.length ? `<div class="table-scroll"><table><caption class="sr-only">Stock levels and expiry information</caption><thead><tr><th>Medication / lot</th><th>Expires</th><th class="numeric">Available packs</th><th class="numeric">Reorder at</th><th>Stock status</th>${state.user.role === "admin" ? "<th>Action</th>" : ""}</tr></thead><tbody>${rows.map(p => `<tr><td><strong>${esc(p.name)} <span class="strength">${esc(p.strength)}</span></strong><span class="cell-secondary">${esc(p.lot)} · ${esc(p.code)}</span></td><td class="${p.availability === "expired" ? "danger-text" : ""}">${dateLabel(p.expires_on)}</td><td class="numeric strong">${p.stock}</td><td class="numeric muted">${p.reorder_level}</td><td>${badge(p.availability)}</td>${state.user.role === "admin" ? `<td><button class="text-button" data-action="edit-stock" data-product="${esc(p.id)}">${icon("edit")} Adjust<span class="sr-only"> ${esc(p.name)}</span></button></td>` : ""}</tr>`).join("")}</tbody></table></div>` : empty("No inventory matches", "Try another search or change the availability filter.", '<a class="button secondary" href="/inventory">Show all inventory</a>')}</section>${data.history.length ? `<section class="panel history-panel"><h2>Recent stock adjustments</h2><div class="table-scroll"><table><caption class="sr-only">Inventory audit history</caption><thead><tr><th>Medication</th><th>Change in packs</th><th>Reason</th><th>Changed by</th></tr></thead><tbody>${data.history.map(h => `<tr><td>${esc(h.name)}</td><td>${h.before} → ${h.after}</td><td>${esc(h.reason)}</td><td>${esc(h.by)}</td></tr>`).join("")}</tbody></table></div></section>` : ""}<p class="catalog-note">${icon("alert")} Expired lots are identified separately from available stock. Stock adjustments require administrator access.</p>`;
}

async function render() {
  const generation = ++state.generation;
  if (!state.user) {
    if (location.pathname !== "/login") history.replaceState({}, "", "/login");
    renderLogin();
    return;
  }
  if (["/", "/login"].includes(location.pathname)) history.replaceState({}, "", "/dashboard");
  const route = location.pathname;
  document.title = `${({ "/dashboard": "Overview", "/catalog": "Medication catalog", "/cart": "Order cart", "/orders": "Orders & tracking", "/inventory": "Inventory" }[route] || "Order details")} · MediSupply`;
  if (!app.querySelector(".app-shell")) shell('<div class="loading-state" role="status">Loading your workspace…</div>');
  else document.querySelector("#main").setAttribute("aria-busy", "true");
  try {
    const endpoints = { "/dashboard": "/api/dashboard", "/catalog": "/api/catalog" + location.search, "/cart": "/api/cart", "/orders": "/api/orders", "/inventory": "/api/inventory" };
    const endpoint = endpoints[route] || (route.startsWith("/orders/MS-") ? "/api" + route : null);
    if (!endpoint) {
      shell(empty("Page not found", "Choose a workspace page from the navigation.", '<a class="button primary" href="/dashboard">Back to overview</a>'));
      return;
    }
    const data = await api(endpoint);
    if (generation !== state.generation) return;
    state.page = data;
    const views = { "/dashboard": dashboard, "/catalog": catalog, "/cart": cartPage, "/orders": ordersPage, "/inventory": inventoryPage };
    if (route === "/cart") state.cart = data;
    shell(views[route] ? views[route](data) : orderDetail(data.order));
    document.querySelector("#main").focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "instant" });
  } catch (error) {
    if (generation === state.generation && state.user) shell(errorPanel(error));
  }
}

function cartItems() { return (state.cart?.lines || []).map(l => ({ product_id: l.id, quantity: l.quantity })); }
async function updateCart(items, code = state.cart?.discount_code || "") {
  state.cart = await send("/api/cart", "PUT", { items, discount_code: code });
  const count = document.querySelector(".cart-count");
  if (count) count.textContent = state.cart.lines.reduce((sum, l) => sum + l.quantity, 0);
}

function confirmCancellation(orderId) {
  const dialog = document.querySelector("#confirm-dialog");
  dialog.innerHTML = `<div class="dialog-heading"><h2 id="confirm-title">Cancel order ${esc(orderId)}?</h2><button class="icon-button" data-action="close-dialog" aria-label="Close confirmation">${icon("close")}</button></div><p>Eligible orders will release their reserved stock. This action cannot be undone.</p><div id="dialog-error" class="form-error" role="alert"></div><div class="dialog-actions"><button class="button secondary" data-action="close-dialog">Keep order</button><button class="button danger" data-action="confirm-cancel" data-order="${esc(orderId)}">Confirm cancellation</button></div>`;
  dialog.showModal();
}

function editStock(pid) {
  const product = state.page.products.find(p => p.id === pid);
  if (!product) return;
  const dialog = document.querySelector("#confirm-dialog");
  dialog.innerHTML = `<div class="dialog-heading"><h2 id="confirm-title">Adjust stock</h2><button class="icon-button" data-action="close-dialog" aria-label="Close stock adjustment">${icon("close")}</button></div><p><strong>${esc(product.name)} ${esc(product.strength)}</strong><br>Lot ${esc(product.lot)} · currently ${product.stock} packs</p><form id="stock-form" data-product="${esc(pid)}"><div class="form-field"><label for="new-stock">Available packs</label><input id="new-stock" type="number" name="stock" min="0" max="100000" step="1" required value="${product.stock}"></div><div class="form-field"><label for="adjustment-reason">Adjustment reason</label><input id="adjustment-reason" name="reason" minlength="3" maxlength="200" required placeholder="e.g. Warehouse receipt confirmed"></div><div id="dialog-error" class="form-error" role="alert"></div><div class="dialog-actions"><button type="button" class="button secondary" data-action="close-dialog">Cancel</button><button type="submit" class="button primary">Save stock</button></div></form>`;
  dialog.showModal();
}

document.addEventListener("click", async event => {
  const link = event.target.closest("a[href]");
  if (link && link.getAttribute("href").startsWith("/") && !event.ctrlKey && !event.metaKey && !event.shiftKey) {
    event.preventDefault();
    navigate(link.getAttribute("href"));
    return;
  }
  const button = event.target.closest("[data-action]");
  if (!button || button.disabled) return;
  const action = button.dataset.action;
  if (action === "dismiss-toast") { document.querySelector("#notifications").innerHTML = ""; return; }
  if (action === "login-role") { state.loginRole = button.dataset.role; renderLogin(); return; }
  if (action === "retry") { render(); return; }
  if (action === "close-dialog") { document.querySelector("#confirm-dialog").close(); return; }
  if (action === "cancel-order") { confirmCancellation(button.dataset.order); return; }
  if (action === "edit-stock") { editStock(button.dataset.product); return; }
  button.disabled = true;
  try {
    if (action === "logout") {
      await send("/api/logout", "POST", {});
      state.user = null;
      state.cart = null;
      state.checkoutDraft = { purchase_order: "", notes: "" };
      await navigate("/login");
    } else if (action === "remove-line") {
      await updateCart(cartItems().filter(l => l.product_id !== button.dataset.product));
      await render();
      notify("Medication removed from your cart.");
    } else if (action === "clear-cart") {
      await updateCart([]);
      await render();
    } else if (action === "remove-discount") {
      await updateCart(cartItems(), "");
      await render();
      notify("Discount removed.");
    } else if (action === "confirm-cancel") {
      await send("/api/orders/cancel", "POST", { order_id: button.dataset.order });
      document.querySelector("#confirm-dialog").close();
      await render();
      notify("Order cancelled. Reserved stock has been released.");
    } else if (action === "advance-order") {
      await send("/api/orders/status", "PATCH", { order_id: button.dataset.order, status: button.dataset.status });
      await render();
      notify(`Order marked as ${button.dataset.status}.`);
    }
  } catch (error) {
    const dialogError = document.querySelector("#confirm-dialog[open] #dialog-error");
    if (dialogError) dialogError.textContent = error.message;
    else notify(error.message, "error");
  } finally { if (button.isConnected) button.disabled = false; }
});

document.addEventListener("submit", async event => {
  const form = event.target;
  event.preventDefault();
  if (["catalog-filters", "order-filters", "inventory-filters"].includes(form.id)) {
    const params = new URLSearchParams();
    for (const [key, value] of new FormData(form)) if (value.trim()) params.set(key, value.trim());
    await navigate(location.pathname + (params.size ? "?" + params : ""));
    return;
  }
  const button = event.submitter || form.querySelector('[type="submit"]');
  if (button?.disabled) return;
  if (button) { button.disabled = true; button.setAttribute("aria-busy", "true"); }
  const values = Object.fromEntries(new FormData(form));
  form.querySelector(".form-error")?.replaceChildren();
  try {
    if (form.id === "login-form") {
      const data = await send("/api/login", "POST", values);
      state.user = data.user;
      state.cart = await api("/api/cart");
      await navigate("/dashboard");
    } else if (form.classList.contains("add-form")) {
      const pid = form.dataset.product;
      const items = cartItems();
      const line = items.find(l => l.product_id === pid);
      if (line) line.quantity += Number(values.quantity);
      else items.push({ product_id: pid, quantity: Number(values.quantity) });
      await updateCart(items);
      notify(`${values.quantity} ${Number(values.quantity) === 1 ? "pack" : "packs"} added to your order cart.`);
    } else if (form.classList.contains("quantity-form")) {
      await updateCart(cartItems().map(l => l.product_id === form.dataset.product ? { ...l, quantity: Number(values.quantity) } : l));
      await render();
      notify("Order quantity updated.");
    } else if (form.id === "discount-form") {
      await updateCart(cartItems(), values.code);
      await render();
      notify(values.code.trim() ? "Discount applied to your order." : "Discount removed.");
    } else if (form.id === "checkout-form") {
      if (!form.dataset.requestId) form.dataset.requestId = crypto.randomUUID();
      const data = await send("/api/orders", "POST", { ...values, items: cartItems(), discount_code: state.cart.discount_code, idempotency_key: form.dataset.requestId });
      state.cart = null;
      state.checkoutDraft = { purchase_order: "", notes: "" };
      await navigate("/orders/" + data.order.id);
      notify(`Order ${data.order.id} submitted successfully.`);
    } else if (form.id === "stock-form") {
      await send("/api/inventory", "PATCH", { product_id: form.dataset.product, stock: Number(values.stock), reason: values.reason });
      document.querySelector("#confirm-dialog").close();
      await render();
      notify("Inventory updated. The adjustment has been recorded.");
    }
  } catch (error) {
    const field = form.querySelector(".form-error");
    if (field) field.textContent = error.message;
    else notify(error.message, "error");
  } finally {
    if (button?.isConnected) { button.disabled = false; button.removeAttribute("aria-busy"); }
  }
});

document.addEventListener("input", event => {
  const input = event.target;
  if (input.form?.id === "checkout-form" && ["purchase_order", "notes"].includes(input.name)) {
    state.checkoutDraft[input.name] = input.value;
  }
});
window.addEventListener("popstate", render);
async function start() {
  try {
    const session = await api("/api/session");
    state.user = session.user;
    state.businessDate = session.business_date;
    if (state.user) {
      try { state.cart = await api("/api/cart"); } catch { state.cart = null; }
    }
    await render();
  } catch (error) {
    app.innerHTML = `<main id="main" class="boot">${errorPanel(error)}</main>`;
    app.querySelector('[data-action="retry"]').addEventListener("click", start, { once: true });
  }
}
start();
