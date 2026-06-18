"""Shared validation for bin payloads (API + CSV import)."""
from __future__ import annotations

from typing import List, Tuple

from backend_api.schemas.api_models import BinCreate


def validate_bin_row(b: BinCreate) -> Tuple[bool, str]:
    if b.id < 1:
        return False, "id must be >= 1"
    if not b.location or not str(b.location).strip():
        return False, "location is required"
    if not (-90 <= b.lat <= 90):
        return False, "lat must be between -90 and 90"
    if not (-180 <= b.lon <= 180):
        return False, "lon must be between -180 and 180"
    if not (0 <= b.fill_level <= 100):
        return False, "fill_level must be 0..100"
    if b.gas_level < 0 or b.gas_level > 5000:
        return False, "gas_level out of range (0..5000)"
    if not (-50 <= b.temp <= 80):
        return False, "temp out of range (-50..80)"
    if not (0 <= b.battery <= 100):
        return False, "battery must be 0..100"
    if not (0 <= b.moisture <= 100):
        return False, "moisture must be 0..100"
    if not b.tenant_id or not str(b.tenant_id).strip():
        return False, "tenant_id is required"
    tid = str(b.tenant_id).strip()
    if len(tid) > 64 or any(c in tid for c in [";", "'", '"', "--"]):
        return False, "tenant_id has invalid characters"
    return True, ""


def validate_bulk(bins: List[BinCreate]) -> Tuple[bool, str, List[int]]:
    if len(bins) == 0:
        return False, "empty list", []
    if len(bins) > 2000:
        return False, "maximum 2000 bins per request", []
    seen: set[int] = set()
    bad_ids: List[int] = []
    for b in bins:
        ok, msg = validate_bin_row(b)
        if not ok:
            return False, f"bin id={b.id}: {msg}", bad_ids
        if b.id in seen:
            bad_ids.append(b.id)
        seen.add(b.id)
    if bad_ids:
        return False, f"duplicate ids in payload: {sorted(set(bad_ids))[:20]}", bad_ids
    return True, "", []
