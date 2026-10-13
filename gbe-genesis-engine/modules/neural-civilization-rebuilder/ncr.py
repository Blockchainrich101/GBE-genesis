"""GBE-NCR-001: deterministic, sandboxed population replay (stdlib only)."""
from dataclasses import dataclass, asdict
import hashlib
import json

@dataclass(frozen=True)
class Agent:
    id: int
    resources: int = 10

def digest(agents):
    payload = json.dumps([asdict(a) for a in agents], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()

def reconstruct(population=1000, events=()):
    if not isinstance(population, int) or not 0 <= population <= 100000:
        raise ValueError("population must be an integer from 0 to 100000")
    state = {i: 10 for i in range(population)}
    for event in events:
        if set(event) != {"agent_id", "delta"}:
            raise ValueError("event requires agent_id and delta")
        i, delta = event["agent_id"], event["delta"]
        if type(i) is not int or i not in state or type(delta) is not int:
            raise ValueError("invalid agent or delta")
        state[i] = max(0, state[i] + delta)
    agents = [Agent(i, state[i]) for i in range(population)]
    return {"population": population, "total_resources": sum(state.values()),
            "state_sha256": digest(agents), "events_applied": len(events)}
