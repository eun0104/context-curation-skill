# Relay Parser — Agent Instructions

## Session start

1. Read `docs/handoff.md`.
2. Read `plan.md`.
3. Check `docs/decisions.md` before changing retry behavior.

## Invariants

- Never send fixture payloads to a real endpoint.

## Read on demand

| Read this | When |
|---|---|
| `docs/decisions.md` | Before changing retry behavior |

## Project shape

This project normalizes archived relay events into a stable JSON record.
