# ADR-002: AWS Service Selection Rationale

**Date:** 2026-04-21  
**Status:** Accepted

---

## Context

EventFlow requires a cloud-native event bus and supporting infrastructure to lift the Python service layer from an in-memory implementation to a production AWS deployment, requiring explicit decisions about which AWS services to use and how to define the infrastructure as code.

---

## Decisions

### 1. EventBridge over SNS

**Decision:** Use EventBridge.

**Alternatives considered:** SNS

**Rationale:** EventBridge gives you content-based routing on event payload fields, a schema registry, event replay via archives, and native integration with 200+ AWS services as sources. SNS gives you topic-based fan-out with no content awareness. For an EDA system with multiple event types that need routing to differ

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
