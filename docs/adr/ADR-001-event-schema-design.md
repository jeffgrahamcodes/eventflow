# ADR-001: Event Schema Design

**Date:** 2026-03-27  
**Status:** Accepted

---

## Context

EventFlow requires a consistent event schema layer that all four services
produce and consume. Before writing any service code, we needed to establish
how events are defined, named, structured, and validated across the system.

---

## Decisions

### 1. Pydantic v2 over dataclasses

**Decision:** Use Pydantic v2 `BaseModel` for all event classes.

**Alternatives considered:** Python `dataclasses`, `TypedDict`

**Rationale:** Pydantic v2 provides field validation, JSON serialization via
`model_dump_json()`, and deserialization via `model_validate_json()` out of
the box. Dataclasses provide none of these. The wire format requirement —
events must serialize cleanly to JSON for EventBridge — makes Pydantic the
clear choice.

---

### 2. Event naming convention

**Decision:** PascalCase for class names, dot-notation past tense for
`event_type` string values.

**Examples:**

- Class: `OrderPlaced`, wire format: `"order.placed"`
- Class: `PaymentFailed`, wire format: `"payment.failed"`

**Rationale:** PascalCase is idiomatic Python for class names. Dot-notation
lowercase maps directly to EventBridge `detail-type` pattern matching. Past
tense reflects that events are facts that already happened, not commands.

---

### 3. Envelope fields on every event

**Decision:** Every event carries these fields regardless of domain:

- `event_id` — unique ID for this event instance
- `event_type` — dot-notation wire format string
- `version` — schema version for future compatibility
- `timestamp` — when the event was created
- `correlation_id` — ties all events in a single order chain together

**Rationale:** These fields enable tracing, routing, and schema evolution
without modifying domain payload fields. `correlation_id` is the critical
one — it allows a single order to be traced across all four services in
distributed tracing.

**Key decision:** `correlation_id` uses `default_factory=uuid4` only on
`OrderPlaced` (the originator). All downstream events require it to be
passed in explicitly — enforcing the tracing chain at the type level.

---

### 4. File organization

**Decision:** One file per domain — `order_events.py`, `payment_events.py`,
`inventory_events.py`, `notification_events.py`.

**Alternatives considered:** Single `events.py` file, one file per class.

**Rationale:** Single file becomes unwieldy as the schema grows. One file
per class is excessive for a project this size. One file per domain groups
related events together and mirrors the service boundaries.

---

### 5. StrEnum for constrained string fields

**Decision:** Use `StrEnum` for fields with a finite set of valid values:
`CancellationReason`, `PaymentFailureReason`, `NotificationReason`.

**Alternatives considered:** Raw `str` with `field_validator`, `Literal` types.

**Rationale:** `StrEnum` values are plain strings on the wire, enforced by
Pydantic at the boundary, and self-documenting in the code. A raw `str`
field requires a manual validator and allows invalid values to slip through
if the validator is forgotten. `StrEnum` makes invalid values impossible.

---

## Consequences

- All event classes follow the same envelope + payload structure
- Adding a new event requires defining it in the correct domain file and
  exporting it from `__init__.py`
- Changing an existing event schema is a breaking change — consumers depend
  on field names and types
- `version` field exists to support future schema evolution if breaking
  changes are required

---

## Addendum: OrderValidated Schema Update

**Date:** 2026-04-02  
**Status:** Accepted

### Context

During implementation of InventoryService (EF-010), it became clear that
`OrderValidated` did not carry enough context for downstream consumers to
act without looking up additional state. Specifically, InventoryService
needs to know which items were ordered to check stock availability — but
that information only existed on `OrderPlaced`.

### Decision

Add `items: list[dict]` to `OrderValidated`, threaded forward from
`OrderPlaced` in the `validate_order` handler.

### Alternatives Considered

**Have InventoryService subscribe to `order.placed` directly** — rejected
because stock reservation should only happen after validation passes.
Subscribing to `OrderPlaced` would allow stock to be reserved for invalid
orders.

**Have InventoryService look up order items from a data store** — rejected
because no data store exists in Phase 1, and adding a direct lookup
dependency would couple InventoryService to a storage layer unnecessarily
at this stage.

### Consequences

- `OrderValidated` now carries the full items list from `OrderPlaced`
- All downstream consumers of `OrderValidated` have access to order items
  without additional lookups
- Any existing tests constructing `OrderValidated` without `items` must be
  updated to include the field
- This pattern — carrying relevant context forward on events — is now the
  established convention for EventFlow
---

## Addendum 2: OrderCancelled items field and _pending_items pattern

**Date:** 2026-04-05  
**Status:** Accepted

### Context

During implementation of `release_stock()` in InventoryService (EF-010),
it became clear that `OrderCancelled` needed to carry the order items so
InventoryService could restore the correct quantities back to the inventory
store. The items payload only existed on `OrderPlaced` and `OrderValidated`.

### Decision

Add `items: list[dict]` to `OrderCancelled`. Rather than threading items
through every intermediate event (`PaymentFailed`, `StockInsufficient`),
`OrderService` maintains an internal `_pending_items` dictionary that maps
`order_id` to items while an order is in flight.

`handle_order_validated` stores the items:
```python
self._pending_items[event.order_id] = event.items
```

Each terminal handler retrieves and removes them with `.pop()`:
```python
items = self._pending_items.pop(event.order_id, [])
```

### Alternatives Considered

**Thread `items` through every downstream event** — rejected because it
would require adding `items` to `PaymentFailed`, `StockInsufficient`, and
any future failure events. Each intermediate event would carry payload it
does not need for its own purpose, bloating the wire format.

### Consequences

- `OrderCancelled` now carries `items` — all constructions must include it
- `OrderService` is stateful — it holds in-flight order data in memory
- `.pop()` on terminal states prevents memory leaks in long-running processes
- This pattern is appropriate for Phase 1 — in Phase 2 this state moves to
  DynamoDB where it survives Lambda cold starts and container recycling

---

## Addendum 3: total_amount threading through OrderValidated and StockReserved

**Date:** 2026-04-05  
**Status:** Accepted

### Context

During implementation of PaymentService (EF-011), it became clear that
`StockReserved` did not carry the order total amount that PaymentService
needs to charge the customer. The total amount only existed on `OrderPlaced`.

### Decision

Add `total_amount: float` to both `OrderValidated` and `StockReserved`,
threading it forward from `OrderPlaced` through the event chain:

`OrderPlaced.total_amount` → `OrderValidated.total_amount` → `StockReserved.total_amount` → `PaymentService.charge()`

### Alternatives Considered

**Store `total_amount` in `InventoryService._pending_amounts`** — rejected
because `total_amount` is a natural property of a stock reservation. An
order worth a specific amount is being reserved. The amount belongs on the
event, not in service state.

**Have PaymentService look up the order total from a data store** — rejected
because no data store exists in Phase 1, and adding a lookup dependency
would couple PaymentService to storage unnecessarily at this stage.

### Consequences

- `OrderValidated` and `StockReserved` now carry `total_amount`
- All existing constructions of both events must include `total_amount`
- PaymentService can charge the correct amount directly from `StockReserved`
- In Phase 2, `total_amount` on the event becomes the authoritative charge
  amount — the DynamoDB order record serves as the audit trail

---

## Addendum 4: PaymentService _pending_charges pattern for refund amount

**Date:** 2026-04-05  
**Status:** Accepted

### Context

During implementation of `refund()` in PaymentService (EF-011), it became
clear that `OrderCancelled` does not carry the original charge amount needed
to issue a refund. The charge amount only exists on `PaymentCharged`, which
fires earlier in the pipeline.

### Decision

PaymentService maintains an internal `_pending_charges` dictionary that maps
`order_id` to `charge_amount` while a payment is in flight.

`handle_payment_charged` stores the amount: `self._pending_charges[event.order_id] = event.charge_amount`

`refund()` retrieves and removes it with `.pop()`: `refund_amount = self._pending_charges.pop(event.order_id, 0.0)`

### Alternatives Considered

**Add `charge_amount` to `OrderCancelled`** — rejected because
`OrderCancelled` is emitted by `OrderService` which has no knowledge of
whether a payment was charged or how much it was. Adding payment data to
an order event violates the service boundary — payment concerns belong in
`PaymentService`, not in `OrderService`.

**Have PaymentService look up the charge amount from a data store** —
rejected because no data store exists in Phase 1. In Phase 2 the charge
amount will be stored in DynamoDB and this pattern will be replaced by a
direct lookup.

### Consequences

- `PaymentService` is stateful — it holds in-flight charge amounts in memory
- `PaymentService` subscribes to `payment.charged` to capture its own output
- `.pop()` on `refund()` prevents memory leaks in long-running processes
- `0.0` as the default in `.pop()` handles the edge case where `refund()`
  fires for an order that was never charged — no payment was taken so no
  refund is issued
- In Phase 2 this state moves to DynamoDB where it survives Lambda cold
  starts and container recycling