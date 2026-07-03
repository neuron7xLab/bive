"""Evidence-chain integrity — a deterministic, reproducible fingerprint.

For a dossier to enter an operational or legal chain of custody it must be
*reproducible* and *tamper-evident*: anyone holding the original source text can
regenerate the exact same review and confirm the fingerprint. This computes:

* ``source_sha256`` — hash of the exact source text analysed;
* ``analysis_sha256`` — hash of the canonical analysis output (minus the
  integrity block itself);
* ``case_id`` — a short combined identifier over both.

No timestamps or random values enter the hash — same input, same fingerprint,
forever. A single altered character in the source or a tampered analysis changes
the hash, which is the point.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# Bump when the analysis semantics change so fingerprints are version-scoped.
COGVERITAS_ENGINE = "cogveritas/1"


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonical(payload: dict[str, Any]) -> str:
    """Deterministic JSON: sorted keys, no incidental whitespace, unicode intact."""
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def source_sha256(text: str) -> str:
    return _sha256(text)


def analysis_sha256(output_payload: dict[str, Any]) -> str:
    """Hash of the analysis output with the integrity block excluded."""
    payload = {k: v for k, v in output_payload.items() if k != "integrity"}
    return _sha256(_canonical(payload))


def compute_integrity(text: str, output_payload: dict[str, Any]) -> dict[str, str]:
    """The integrity block for a source/analysis pair — deterministic."""
    src = source_sha256(text)
    ana = analysis_sha256(output_payload)
    case_id = _sha256(f"{src}:{ana}")[:16]
    return {
        "engine": COGVERITAS_ENGINE,
        "source_sha256": src,
        "analysis_sha256": ana,
        "case_id": case_id,
    }
