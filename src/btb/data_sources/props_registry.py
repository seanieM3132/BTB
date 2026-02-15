from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from btb.data_sources.props_normalize import normalize_props_fixture


def ingest_props_from_fixture(path: str) -> dict[str, Any]:
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        return {"ok": False, "error": "props fixture payload must be a JSON object"}
    norm = normalize_props_fixture(payload)
    return {"ok": True, "fixture": str(p), "normalized": norm}
