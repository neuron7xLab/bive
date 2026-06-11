from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

LOGGER = logging.getLogger("bive")


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def log_event(event: str, **fields: Any) -> None:
    """Emit one structured UTC JSON operational log event.

    The logger deliberately receives only metadata supplied by call sites; transcript text and
    report bodies should not be passed here.
    """

    payload = {"timestamp": utc_timestamp(), "event": event, **fields}
    LOGGER.info(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
