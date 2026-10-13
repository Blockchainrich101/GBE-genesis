# NCR-001 integration boundary — proposed, not activated

Source architecture: repository-root GBE_GIE_Architecture.md and GIE_Deep_Dive.md on main.

## Architecture mapping

- Director AI: routes approved reconstruction requests; NCR must not self-dispatch.
- Agent Manager: controls module lifecycle and resource quotas.
- Governance: Class A (Observe) for offline simulation; any external effect requires a separate approval path.
- Knowledge/Memory: may supply approved snapshots; no direct writes from NCR.
- Verification: attach source revision, fixture digest, final state digest, environment, and execution result before accepting an output.
- Model Gateway: required for any future neural model; current prototype has no model calls.

## Proposed input contract

`{request_id, population, events, snapshot_id, authorization_class: "A"}`

## Proposed output contract

`{request_id, population, events_applied, total_resources, state_sha256, source_revision, receipt_id}`

These are design proposals only. No runtime consumer, registration API, or receipt storage implementation has been confirmed.

## Gate before wiring

1. Identify actual consumer code and callable registration interface.
2. Confirm authorization, schema, persistence and receipt APIs.
3. Implement adapter against that real interface; reject unknown schemas.
4. Run end-to-end fixture replay with independent verification.
5. Retain draft PR until review and accepted receipt.
