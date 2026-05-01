# ADR-002: AWS Service Selection

**Date:** 2026-05-01
**Status:** Accepted

---

## Context

EventFlow requires a cloud-native event bus and supporting infrastructure
to lift the Python service layer from an in-memory implementation to a
production AWS deployment, requiring explicit decisions about which AWS
services to use and how to define the infrastructure as code.

---

## Decisions

### 1. EventBridge over SNS

**Decision:** Use Amazon EventBridge as the event bus.

**Alternatives considered:** Amazon SNS

**Rationale:** EventBridge routes on event content, specifically the
`detail-type` field, which maps directly to EventFlow's event type strings
(`order.validated`, `payment.charged`, etc.). Each event type routes to a
different consumer queue with a single rule. SNS is topic-based. To achieve
the same routing you would need one topic per event type, resulting in 10+
topics and significantly more infrastructure to manage. EventBridge also
provides a native event archive for replay, a schema registry for
documentation, and direct integration with 200+ AWS services as event
sources. For a system with multiple event types each requiring different
routing, EventBridge is the clear choice.

**Consequences:**

- EventBridge `detail-type` must match the `event_type` string on every
  Pydantic event model exactly (the convention established in ADR-001 is
  what makes this work)
- Event archive enables replay against new consumers without re-publishing
  events
- Custom bus provides isolation from AWS service events on the default bus

---

### 2. SQS as the buffer between EventBridge and Lambda

**Decision:** Route EventBridge events to SQS queues, which trigger Lambda
functions via event source mappings, rather than invoking Lambda directly
from EventBridge.

**Alternatives considered:** Direct Lambda invocation from EventBridge

**Rationale:** EventBridge can invoke Lambda directly but doing so removes
the retry and buffering guarantees that SQS provides. SQS gives each
consumer service its own queue with configurable visibility timeout,
automatic retries up to `maxReceiveCount`, and a Dead Letter Queue for
messages that fail repeatedly. Direct Lambda invocation from EventBridge
has limited retry behavior and no DLQ support. For a production system
where failed event processing must be captured and investigated rather than
silently dropped, SQS is required.

**Consequences:**

- Each consumer service has a main queue and a DLQ, 8 queues total
- Failed messages are preserved in the DLQ after 3 failed attempts
- Visibility timeout set to 6x Lambda timeout to prevent duplicate
  processing during retries
- SQS adds a small amount of latency compared to direct invocation (acceptable for an order processing system that is not latency-critical)

---

### 3. CDK over CloudFormation and Terraform

**Decision:** Use AWS CDK (TypeScript) for infrastructure as code.

**Alternatives considered:** Raw CloudFormation (YAML), Terraform

**Rationale:** CDK generates CloudFormation under the hood but expresses
infrastructure as real TypeScript code, with type safety, IDE
autocomplete, and reusable constructs. Raw CloudFormation requires verbose
YAML with manual resource references. Terraform is excellent but requires
a separate state management setup and is not AWS-native. CDK's grant
methods (`grantPutEventsTo`, `grantConsumeMessages`) handle IAM policy
generation automatically, reducing the surface area for misconfiguration.
CDK also supports L3 constructs, reusable abstractions over multiple AWS
resources, which is the foundation of the developer platform layer in
Phase 3.

**Consequences:**

- Infrastructure is defined in TypeScript alongside Python source in the
  same monorepo
- CDK requires Node.js and npm in the development environment
- `cdk synth` validates infrastructure before deployment, equivalent to
  `mypy` for infrastructure code
- Docker is required for Lambda bundling via `PythonFunction`

---

### 4. Custom EventBridge bus over the default bus

**Decision:** Create a dedicated `eventflow-dev-bus` rather than using the
AWS default event bus.

**Alternatives considered:** Default EventBridge event bus

**Rationale:** The default event bus receives events from AWS services
(EC2 state changes, CodePipeline events, etc.) as well as custom events.
Using it for EventFlow events would mix application events with AWS
infrastructure events, complicating routing rules and event archive queries.
A custom bus provides complete isolation, only EventFlow events are on it,
routing rules are unambiguous, and the archive contains only application
events.

**Consequences:**

- All EventFlow services must publish to the custom bus ARN explicitly
- Custom bus ARN is exported as a CloudFormation output for reference
- Event archive on the custom bus captures only EventFlow events

---

### 5. PythonFunction over standard Lambda Function

**Decision:** Use `@aws-cdk/aws-lambda-python-alpha` `PythonFunction`
construct for Lambda definitions.

**Alternatives considered:** Standard `aws-cdk-lib/aws-lambda` `Function`
with manual bundling

**Rationale:** `PythonFunction` automatically bundles Python dependencies
using Docker and the official AWS Lambda build image, ensuring compiled
dependencies are built for the correct Amazon Linux runtime. The standard
`Function` construct requires manual zip creation and dependency bundling.
`PythonFunction` reads `pyproject.toml` and handles packaging automatically, consistent with the `uv`-based development workflow established in
Sprint 1.

**Consequences:**

- Docker must be running during `cdk synth` and `cdk deploy`
- First synth is slower due to Docker image pull, subsequent synths use
  the cached image
- `assetExcludes` must be configured to prevent `cdk.out` and
  `node_modules` from being included in the Lambda package
- Handler path follows the module convention:
  `infra.lambda.handler_name.handler`

---

## Summary

| Decision         | Choice               | Key Reason                            |
| ---------------- | -------------------- | ------------------------------------- |
| Event bus        | EventBridge          | Content-based routing on detail-type  |
| Consumer buffer  | SQS + DLQ            | Retry guarantees and DLQ for failures |
| IaC tool         | AWS CDK (TypeScript) | Type safety and L3 construct support  |
| Event bus type   | Custom bus           | Isolation from AWS service events     |
| Lambda packaging | PythonFunction       | Automatic dependency bundling         |
