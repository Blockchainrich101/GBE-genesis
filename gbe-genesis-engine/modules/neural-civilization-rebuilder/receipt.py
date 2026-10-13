"""Evidence envelope for NCR fixture replay; does not grant Genesis acceptance."""
import hashlib
import json

def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

def make_receipt(request_id, population, events, result, source_revision, python_version):
    if not all(isinstance(x, str) and x.strip() for x in
               (request_id, source_revision, python_version)):
        raise ValueError("request, revision and runtime identifiers required")
    if not isinstance(population, int) or isinstance(population, bool) or population < 0:
        raise ValueError("invalid population")
    if not isinstance(events, (tuple, list)):
        raise ValueError("events must be a sequence")
    if not isinstance(result, dict) or result.get("population") != population or result.get("events_applied") != len(events):
        raise ValueError("result does not match request")
    state_hash = result.get("state_sha256")
    if not isinstance(state_hash, str) or len(state_hash) != 64 or any(c not in "0123456789abcdef" for c in state_hash):
        raise ValueError("invalid state digest")
    receipt = {
        "schema": "gbe.ncr.fixture-receipt.v1",
        "status": "unaccepted_fixture_evidence",
        "request_id": request_id,
        "source_revision": source_revision,
        "python_version": python_version,
        "population": population,
        "events_sha256": _sha(events),
        "events_applied": len(events),
        "state_sha256": state_hash,
        "total_resources": result["total_resources"],
    }
    return {**receipt, "receipt_sha256": _sha(receipt)}
