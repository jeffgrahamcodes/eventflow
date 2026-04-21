# ADR-002: AWS Service Selection Rationale

**Date:** 2026-04-21  
**Status:** Accepted

---

## Context

EventFlow requires a cloud-native event bus and supporting infrastructure to lift the Python service layer from an in-memory implementation to a production AWS deployment, requiring explicit decisions about which AWS services to use and how to define the infrastructure as code.

---

## Decisions

### 1. EventBridge over SNS

**Decision:** Use Amazon EventBridge as the event bus.

**Alternatives considered:** Amazon SNS

**Rationale:** EventBridge routes on event content, specifically the `detail-type` field, which maps directly to EventFlow's event type strings (`order.validated`, `payment.charged`, etc.). Each event type routes to a different consumer queue with a single rule. SNS is topic-based. To achieve the same routing you would need one topic per event type, resulting in 10+ topics and significantly more infrastructure to manage. EventBridge also provides a native event archive for replay, a schema registry for documentation, and direct integration with 200+ AWS services as event sources. For a system with multiple event types each requiring different routing, EventBridge is the clear choice.

**Consequences:**

- EventBridge `detail-type` must match the `event_type` string on every Pydantic event model exactly — the convention established in ADR-001 is what makes this work
- Event archive enables replay against new consumers without re-publishing events
- Custom bus provides isolation from AWS service events on the default bus

---
