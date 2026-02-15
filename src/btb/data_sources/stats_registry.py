from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from btb.data_sources.stats_normalize import normalize_stats_fixture


def ingest_stats_from_fixture(path: str) -> Dict[str, Any]:
    p = Path(path)
    payload = json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        return {"ok": False, "error": "stats fixture payload must be a JSON object"}
    norm = normalize_stats_fixture(payload)
    return {"ok": True, "fixture": str(p), "normalized": norm}
