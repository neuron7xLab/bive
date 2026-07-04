"""Content digest for verification reports — tamper-evidence for shared/stored evidence.

A BIVE report is meant to be reviewed, stored and shared. ``content_digest`` is a
sha256 over the substantive analysis so a recipient can prove the report they hold is
byte-for-byte the analysis that was produced — a changed claim, signal, hypothesis or
status changes the digest.

The digest deliberately excludes three fields so it identifies the *analysis*, not the
record: ``content_digest`` itself (it cannot hash itself), ``report_id`` (a unique
per-session record id, intentionally volatile), and ``created_at`` (wall-clock time).
Two reports of the same transcript therefore carry the same content_digest while keeping
distinct report_ids.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

# Excluded from the digest — at EVERY nesting level — so it encodes the analysis, not
# the record instance or when it was built. report_id is a unique per-session id;
# created_at/generated_at/timestamp are wall-clock stamps (created_at at the top level,
# generated_at inside each provenance record). Stripping them recursively is what makes
# the digest a pure function of the substantive analysis.
EXCLUDED_KEYS = frozenset({"content_digest", "report_id", "created_at", "generated_at", "timestamp"})


def _strip_volatile(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _strip_volatile(v) for k, v in value.items() if k not in EXCLUDED_KEYS}
    if isinstance(value, (list, tuple)):
        return [_strip_volatile(v) for v in value]
    return value


def content_digest(payload: Mapping[str, Any]) -> str:
    """Return the sha256 hex digest of a report payload's substantive content."""
    material = _strip_volatile(dict(payload))
    canonical = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_content_digest(payload: Mapping[str, Any]) -> bool:
    """True iff the payload's stored content_digest matches its recomputed content."""
    stored = payload.get("content_digest")
    return isinstance(stored, str) and stored == content_digest(payload)
