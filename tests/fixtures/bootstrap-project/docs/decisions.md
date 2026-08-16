# Decision Record

## ADR-001: Retry only explicitly retryable relay errors

**Date:** 2026-07-02 · **Status:** accepted · **Session:** 004

**Context:** Some HTTP 200 responses contain an error object, and only some errors are transient.
**Decision:** Retry only when the normalized body sets `retryable: true`.
**Rejected alternatives:** Retry every HTTP 200 error body — permanent schema errors loop forever.
**Consequences:** The parser must inspect the response body before scheduling a retry.
**Revisit if:** the relay service publishes a stable error-code contract.
