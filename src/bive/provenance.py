from __future__ import annotations

from .models import ProvenanceRecord


def to_prov_json(
    records: tuple[ProvenanceRecord, ...] | list[ProvenanceRecord],
) -> dict[str, object]:
    entities: dict[str, object] = {}
    activities: dict[str, object] = {}
    agents: dict[str, object] = {}
    was_generated_by: dict[str, object] = {}
    used: dict[str, object] = {}
    for i, r in enumerate(records):
        entities[r.entity_id] = {"prov:label": r.entity_id}
        activities[f"activity:{i}"] = {"prov:label": r.activity, "prov:time": r.generated_at}
        agents[r.agent] = {"prov:label": r.agent}
        was_generated_by[f"gen:{i}"] = {
            "prov:entity": r.entity_id,
            "prov:activity": f"activity:{i}",
        }
        used[f"use:{i}"] = {"prov:activity": f"activity:{i}", "prov:entity": r.source}
    return {
        "prefix": {"prov": "http://www.w3.org/ns/prov#"},
        "entity": entities,
        "activity": activities,
        "agent": agents,
        "wasGeneratedBy": was_generated_by,
        "used": used,
    }
