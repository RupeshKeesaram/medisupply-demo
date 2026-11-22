# MediSupply

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Pharmacy purchasing staff replenish medicines, review prices and track orders. Distribution administrators monitor lots, expiry dates and stock, and move orders through fulfillment.

## Product Purpose

A compact pharmaceutical ordering portal for pharmacy replenishment and distribution operations. Success is a complete purchase and fulfillment journey with clear pricing, inventory visibility and order history.

## Operating Context

Five connected work areas: dashboard, medication catalog, order creation, inventory, and order tracking. All organizations, accounts, prices and stock are fictional. This is a demonstration application, with no patient records, payments, prescriptions, shipping integrations or clinical advice.

## Capabilities and Constraints

Two roles, persistent orders and stock, lot-level expiry information, quantity and pricing validation, eligibility for cancellation, searchable catalog and deterministic test data. Runs from a Git repository under Radius's existing Docker contract. Browser automation needs native labeled controls and stable URLs. Public quotation endpoints support read-only price and eligibility evaluation; order and inventory mutations require a session.

## Brand Commitments

The application name is MediSupply — Pharmacy Ordering Portal. Pharmaceutical distribution is the domain; McKesson is a relevance reference, not a customer, affiliation or a branding source.

## Product Principles

- Show price, pack size, stock and expiry before an ordering decision.
- Give each order a durable identity and an explicit fulfillment history.
- Keep a small, legible workflow suitable for a short demonstration.
- Requirements describe expected behavior independently of implementation.
