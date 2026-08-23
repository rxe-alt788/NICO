#!/usr/bin/env python3
"""4NICO historical ingestion pipeline.

Builds data/empirical_18m_series.json from authoritative/archive inputs without
silently substituting synthetic observations.

Supported inputs are intentionally adapter-based because several NSW data
sources require credentials, bulk exports, or archive files rather than a
frictionless public historical API.

Environment variables / inputs:
  BOM_ARCHIVE_CSV or BOM_ARCHIVE_URL
      CSV with timestamp + rainfall_mm (10-min preferred; daily accepted and
      provenance records its resolution). Optional beach_id/station columns.
  WATERNSW_ARCHIVE_CSV or WATERNSW_ARCHIVE_URL
      CSV with timestamp plus discharge and/or turbidity fields.
  WATERNSW_SUBSCRIPTION_KEY
      Passed as Ocp-Apim-Subscription-Key when WATERNSW_ARCHIVE_URL is used.
  BEACHWATCH_ARCHIVE_CSV or BEACHWATCH_ARCHIVE_URL
      Historical export. Water temperature/conductivity are retained; turbidity
      is used only if explicitly present in the source.
  IMOS_ARCHIVE_CSV or IMOS_ARCHIVE_URL
      Prepared point-extract CSV containing timestamp, beach_id, sst_c and/or
      upwelling_index. NetCDF extraction belongs upstream of this normalizer.
  DPI_INCIDENTS_JSON or DPI_INCIDENTS_URL
      Authoritative incident/detection JSON when available.

The script is deterministic, audit-friendly and safe for GitHub Actions. Missing
feeds remain null with source-status metadata; they are never imputed as facts.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import statistics
import urllib.request
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
BEACH_FILE = ROOT / "data" / "pilot_beaches.json"
OUTPUT_FILE = ROOT / "data" / "empirical_18m_series.json"
START = datetime.fromisoformat("2025-02-23T00:00:00+11:00")
END = datetime.fromisoformat("2026-08-23T23:59:59+10:00")
STEP = timedelta(hours=1)


def parse_ts(value: str) -> datetime:
    value = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone(timedelta(hours=10)))
    return dt


def safe_float(v: Any) -> Optional[float]:
    if v in (None, "", "NA", "N/A", "null", "None", "-"):
        return None
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def fetch_text(url: str, headers: Optional[Dict[str, str]] = None) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "4NICO-pilot/0.4", **(headers or {})})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read().decode("utf-8")


def read_text_input(path_env: str, url_env: str, headers: Optional[Dict[str, str]] = None) -> tuple[Optional[str], str]:
    path = os.getenv(path_env)
    url = os.getenv(url_env)
    if path:
        p = Path(path)
        return p.read_text(encoding="utf-8"), f"file:{p}"
    if url:
        return fetch_text(url, headers), url
    return None, "not_configured"


def csv_rows(text: str) -> List[Dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def beach_lookup() -> Dict[str, Dict[str, Any]]:
    data = json.loads(BEACH_FILE.read_text(encoding="utf-8"))
    return {b["id"]: b for b in data["beaches"]}


def nearest_hour(dt: datetime) -> datetime:
    dt = dt.astimezone(timezone.utc)
    rounded = dt.replace(minute=0, second=0, microsecond=0)
    if dt.minute >= 30:
        rounded += timedelta(hours=1)
    return rounded


def percentile_rank(values: List[float], value: Optional[float]) -> Optional[float]:
    if value is None or not values:
        return None
    ordered = sorted(values)
    below = sum(1 for x in ordered if x <= value)
    return below / len(ordered)


def rolling_sum(points: List[tuple[datetime, float]], hours: int = 72) -> Dict[datetime, float]:
    out: Dict[datetime, float] = {}
    q: deque[tuple[datetime, float]] = deque()
    total = 0.0
    for ts, val in sorted(points):
        q.append((ts, val)); total += val
        cutoff = ts - timedelta(hours=hours)
        while q and q[0][0] <= cutoff:
            _, old = q.popleft(); total -= old
        out[nearest_hour(ts)] = round(total, 3)
    return out


def ingest_bom(beaches: Dict[str, Any], status: Dict[str, Any]) -> Dict[str, Dict[datetime, Dict[str, Any]]]:
    text, source = read_text_input("BOM_ARCHIVE_CSV", "BOM_ARCHIVE_URL")
    result: Dict[str, Dict[datetime, Dict[str, Any]]] = defaultdict(dict)
    if not text:
        status["bom"] = {"state": "MISSING", "source": source, "note": "Configure BOM_ARCHIVE_CSV/URL. Public BOM 10-minute feed is only a recent rolling product; historical archive must be supplied/exported."}
        return result
    rows = csv_rows(text)
    by_beach: Dict[str, List[tuple[datetime, float]]] = defaultdict(list)
    for r in rows:
        ts_raw = r.get("timestamp") or r.get("datetime") or r.get("time")
        rain = safe_float(r.get("rainfall_mm") or r.get("rain_mm") or r.get("rainfall"))
        if not ts_raw or rain is None: continue
        bid = (r.get("beach_id") or r.get("beachId") or "all").strip()
        by_beach[bid].append((parse_ts(ts_raw), rain))
    for bid in beaches:
        pts = by_beach.get(bid) or by_beach.get("all") or []
        sums = rolling_sum(pts, 72)
        distribution = list(sums.values())
        for ts, v in sums.items():
            if START.astimezone(timezone.utc) <= ts <= END.astimezone(timezone.utc):
                result[bid].setdefault(ts, {}).update({"rain72hMm": v, "rainPct": percentile_rank(distribution, v)})
    status["bom"] = {"state": "LOADED", "source": source, "rows": len(rows), "note": "72h rolling rainfall calculated from supplied observations."}
    return result


def ingest_water(beaches: Dict[str, Any], status: Dict[str, Any]) -> Dict[str, Dict[datetime, Dict[str, Any]]]:
    headers = {}
    if os.getenv("WATERNSW_SUBSCRIPTION_KEY"):
        headers["Ocp-Apim-Subscription-Key"] = os.environ["WATERNSW_SUBSCRIPTION_KEY"]
    text, source = read_text_input("WATERNSW_ARCHIVE_CSV", "WATERNSW_ARCHIVE_URL", headers)
    result: Dict[str, Dict[datetime, Dict[str, Any]]] = defaultdict(dict)
    if not text:
        status["waternsw"] = {"state": "MISSING", "source": source, "note": "Configure WaterNSW archive/export or keyed API endpoint."}
        return result
    rows = csv_rows(text)
    turbidity_values: Dict[str, List[float]] = defaultdict(list)
    parsed = []
    for r in rows:
        ts_raw = r.get("timestamp") or r.get("datetime") or r.get("time")
        if not ts_raw: continue
        bid = (r.get("beach_id") or r.get("beachId") or "all").strip()
        turb = safe_float(r.get("turbidity_ntu") or r.get("turbidity"))
        discharge = safe_float(r.get("discharge_m3s") or r.get("flow_m3s") or r.get("discharge"))
        ts = nearest_hour(parse_ts(ts_raw))
        parsed.append((bid, ts, turb, discharge))
        if turb is not None: turbidity_values[bid].append(turb)
    for bid, ts, turb, discharge in parsed:
        targets = beaches.keys() if bid == "all" else [bid]
        for target in targets:
            if target not in beaches: continue
            vals = turbidity_values.get(bid, [])
            result[target].setdefault(ts, {}).update({"turbidityNtu": turb, "turbidityPct": percentile_rank(vals, turb), "dischargeM3s": discharge})
    status["waternsw"] = {"state": "LOADED", "source": source, "rows": len(rows)}
    return result


def ingest_beachwatch(beaches: Dict[str, Any], status: Dict[str, Any]) -> Dict[str, Dict[datetime, Dict[str, Any]]]:
    text, source = read_text_input("BEACHWATCH_ARCHIVE_CSV", "BEACHWATCH_ARCHIVE_URL")
    result: Dict[str, Dict[datetime, Dict[str, Any]]] = defaultdict(dict)
    if not text:
        status["beachwatch"] = {"state": "MISSING", "source": source, "note": "Configure historical Beachwatch export. Turbidity is only consumed when explicitly present."}
        return result
    rows = csv_rows(text)
    for r in rows:
        ts_raw = r.get("timestamp") or r.get("sample_date") or r.get("date")
        bid = (r.get("beach_id") or r.get("beachId") or "").strip()
        if not ts_raw or bid not in beaches: continue
        ts = nearest_hour(parse_ts(ts_raw))
        result[bid].setdefault(ts, {}).update({
            "waterTempC": safe_float(r.get("water_temperature") or r.get("water_temp_c")),
            "conductivity": safe_float(r.get("conductivity")),
            "turbidityNtuBeachwatch": safe_float(r.get("turbidity") or r.get("turbidity_ntu"))
        })
    status["beachwatch"] = {"state": "LOADED", "source": source, "rows": len(rows)}
    return result


def ingest_imos(beaches: Dict[str, Any], status: Dict[str, Any]) -> Dict[str, Dict[datetime, Dict[str, Any]]]:
    text, source = read_text_input("IMOS_ARCHIVE_CSV", "IMOS_ARCHIVE_URL")
    result: Dict[str, Dict[datetime, Dict[str, Any]]] = defaultdict(dict)
    if not text:
        status["imos"] = {"state": "MISSING", "source": source, "note": "Configure a point-extracted IMOS/BOM marine CSV. Raw NetCDF should be reduced upstream to beach/time points."}
        return result
    rows = csv_rows(text)
    sst_by_beach: Dict[str, List[float]] = defaultdict(list)
    parsed = []
    for r in rows:
        ts_raw = r.get("timestamp") or r.get("datetime") or r.get("time")
        bid = (r.get("beach_id") or r.get("beachId") or "").strip()
        if not ts_raw or bid not in beaches: continue
        sst = safe_float(r.get("sst_c") or r.get("sst")); up = safe_float(r.get("upwelling_index"))
        ts = nearest_hour(parse_ts(ts_raw)); parsed.append((bid, ts, sst, up))
        if sst is not None: sst_by_beach[bid].append(sst)
    for bid, ts, sst, up in parsed:
        baseline = statistics.median(sst_by_beach[bid]) if sst_by_beach[bid] else None
        anomaly = None if sst is None or baseline is None else round(sst - baseline, 3)
        result[bid].setdefault(ts, {}).update({"sstC": sst, "sstAnomaly": anomaly, "upwellingIndex": up})
    status["imos"] = {"state": "LOADED", "source": source, "rows": len(rows), "note": "Pilot anomaly uses supplied-window median until a climatological baseline is configured."}
    return result


def load_incidents(status: Dict[str, Any]) -> List[Dict[str, Any]]:
    text, source = read_text_input("DPI_INCIDENTS_JSON", "DPI_INCIDENTS_URL")
    if text:
        data = json.loads(text)
        incidents = data.get("incidents", data if isinstance(data, list) else [])
        status["incidents"] = {"state": "LOADED", "source": source, "count": len(incidents)}
        return incidents
    status["incidents"] = {"state": "SEED_ONLY", "source": "repository verified-public seed", "note": "Replace/reconcile with DPI/ASID before formal validation."}
    return [
        {"id":"vaucluse-2026-01-18","timestamp":"2026-01-18T16:20:00+11:00","location":"Vaucluse / Shark Beach","beachId":"balmoral","eventClass":"SERIOUS_BITE","provenance":"public-report seed"},
        {"id":"dee-why-2026-01-19","timestamp":"2026-01-19T11:45:00+11:00","location":"Dee Why Beach","beachId":"north-steyne","eventClass":"BOARD_BITE_NO_INJURY","provenance":"public-report seed"},
        {"id":"north-steyne-2026-01-19","timestamp":"2026-01-19T18:20:00+11:00","location":"North Steyne Beach","beachId":"north-steyne","eventClass":"SERIOUS_BITE","provenance":"public-report seed"},
        {"id":"point-plomer-2026-01","timestamp":null,"location":"Point Plomer","beachId":null,"eventClass":"BITE","provenance":"public-report seed; exact timestamp pending authoritative reconciliation"},
        {"id":"coogee-2026-06-13","timestamp":"2026-06-13T11:10:00+10:00","location":"Coogee Beach","beachId":"coogee","eventClass":"SERIOUS_BITE","provenance":"public-report seed"}
    ]


def merge_layers(beaches: Dict[str, Any], layers: Iterable[Dict[str, Dict[datetime, Dict[str, Any]]]]) -> Dict[str, List[Dict[str, Any]]]:
    merged: Dict[str, Dict[datetime, Dict[str, Any]]] = defaultdict(dict)
    for layer in layers:
        for bid, points in layer.items():
            for ts, fields in points.items():
                merged[bid].setdefault(ts, {}).update(fields)
    output = {}
    for bid in beaches:
        output[bid] = [{"timestamp": ts.isoformat().replace("+00:00", "Z"), **fields} for ts, fields in sorted(merged[bid].items())]
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(OUTPUT_FILE))
    args = parser.parse_args()
    beaches = beach_lookup(); status: Dict[str, Any] = {}
    rain = ingest_bom(beaches, status)
    water = ingest_water(beaches, status)
    beachwatch = ingest_beachwatch(beaches, status)
    imos = ingest_imos(beaches, status)
    incidents = load_incidents(status)
    payload = {
        "schemaVersion": "0.4.0",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "evaluationWindow": {"start": START.isoformat(), "end": END.isoformat()},
        "mode": "EMPIRICAL_PARTIAL" if any(v.get("state") == "LOADED" for v in status.values()) else "AWAITING_ARCHIVES",
        "sourceStatus": status,
        "qualityRule": "Null means unavailable. No synthetic environmental value is inserted into this dataset.",
        "incidents": incidents,
        "beaches": merge_layers(beaches, [rain, water, beachwatch, imos])
    }
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "mode": payload["mode"], "sources": status}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
