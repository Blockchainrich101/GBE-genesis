# GBE-NCR-001 — Neural Civilization Rebuilder (prototype)

Deterministic, offline, stdlib-only agent-population state reconstruction. No neural model or civilization forecasting is implemented yet.

Run tests from this directory: `python -m unittest -v test_ncr.py`

API: `reconstruct(population=1000, events=[])`. Events have integer `agent_id` and `delta` fields. Outputs aggregate resource metrics, event count, and SHA-256 of the final ordered agent state.

**Status:** prototype for review. Tests are supplied but not yet verified in GitHub CI. No Genesis consumer integration or verified receipts. No external actions.
