## Session 001 — 2026-06-20

### Did
- Added archive discovery.

### Learned
- [candidate] Vendor archive filenames are case-sensitive even on case-insensitive clients.

## Session 002 — 2026-06-24

### Did
- Added response normalization.

### Learned
- [gotcha] The relay can return HTTP 200 with an error object in the body.

## Session 003 — 2026-06-27

### Did
- Fixed success classification after a fixture was incorrectly accepted.

### Learned
- [gotcha] HTTP status alone cannot classify relay success; inspect the body error field.

## Session 004 — 2026-07-02

### Did
- Added retry classification.

### Learned
- [decision] Retry only when the normalized body says `retryable: true`; permanent schema errors must not loop.

## Session 005 — 2026-07-06

### Did
- Added uppercase archive fixtures.

### Learned
- [candidate] Preserve the source filename's case when resolving archived relay events.

## Session 006 — 2026-07-10

### Did
- Closed M1 and prepared failure-classification work.

### Learned
- [candidate] Success classification requires both HTTP status and the absence of a body error object.
