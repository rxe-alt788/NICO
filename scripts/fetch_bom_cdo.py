#!/usr/bin/env python3
"""Fetch observed daily rainfall from BOM Climate Data Online for Step 1 displacement.

The BOM CDO daily rainfall page generates a temporary ZIP link. This script resolves
that link at runtime, downloads the all-years archive, filters the 4NICO evaluation
window, and writes an adapter-compatible ephemeral raw CSV.

Station 066214 is the current Sydney Observatory Hill site used for the initial
single-gauge Sydney proxy. The output is observed data, not a synthetic fixture.
"""
from __future__ import annotations

import csv
import html
import io
import os
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
OUTPUT = RAW / "bom_rainfall_history.csv"
START = date(2025, 2, 23)
END = date(2026, 8, 23)
DEFAULT_STATION = "066214"
BASE = "https://www.bom.gov.au"
CDO = BASE + "/jsp/ncc/cdio/weatherData/av"
SYDNEY = ZoneInfo("Australia/Sydney")


def request_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "4NICO-validation/0.7"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()


def resolve_zip_url(station: str) -> str:
    params = {
        "p_nccObsCode": "136",
        "p_display_type": "dailyDataFile",
        "p_startYear": "",
        "p_c": "",
        "p_stn_num": station,
    }
    landing = CDO + "?" + urllib.parse.urlencode(params)
    text = request_bytes(landing).decode("utf-8", errors="replace")
    matches = re.findall(r'href=["\']([^"\']*p_display_type=dailyZippedDataFile[^"\']*)["\']', text, flags=re.I)
    if not matches:
        # Older CDO markup sometimes exposes the target outside an href attribute.
        m = re.search(r'(/jsp/ncc/cdio/weatherData/av\?p_display_type=dailyZippedDataFile[^"\'<\s]+)', text, flags=re.I)
        matches = [m.group(1)] if m else []
    if not matches:
        raise RuntimeError(f"BOM CDO did not expose an all-years ZIP link for station {station}")
    return urllib.parse.urljoin(BASE, html.unescape(matches[0]))


def pick_csv_from_zip(blob: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            raise RuntimeError("BOM CDO ZIP contained no CSV")
        preferred = next((n for n in names if "Data" in n or "data" in n), names[0])
        return zf.read(preferred).decode("utf-8-sig", errors="replace")


def first(row: dict[str, str], *names: str) -> str | None:
    lowered = {str(k).strip().lower(): v for k, v in row.items()}
    for name in names:
        v = lowered.get(name.lower())
        if v not in (None, ""):
            return str(v).strip()
    return None


def main() -> int:
    station = os.getenv("BOM_CDO_STATION", DEFAULT_STATION).strip()
    zip_url = resolve_zip_url(station)
    csv_text = pick_csv_from_zip(request_bytes(zip_url))
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    selected = []
    for row in rows:
        y = first(row, "Year")
        m = first(row, "Month")
        d = first(row, "Day")
        rain = first(row, "Rainfall amount (millimetres)", "rainfall_mm", "rainfall")
        quality = first(row, "Quality")
        if not (y and m and d and rain not in (None, "")):
            continue
        try:
            obs_date = date(int(float(y)), int(float(m)), int(float(d)))
            rain_mm = float(rain)
        except (ValueError, TypeError):
            continue
        if not (START <= obs_date <= END):
            continue
        # BOM daily rainfall observations are nominally read at 09:00 local time
        # and describe rainfall accumulated over the preceding observation period.
        timestamp = datetime.combine(obs_date, time(9, 0), tzinfo=SYDNEY).isoformat()
        selected.append({
            "timestamp": timestamp,
            "beach_id": "all",
            "station_id": station,
            "rainfall_mm": f"{rain_mm:.3f}",
            "quality": quality or "",
            "observation_resolution": "daily",
            "synthetic_flag": "false",
            "source_class": "OBSERVED_BOM_CDO_SINGLE_GAUGE_PROXY",
        })

    if not selected:
        raise RuntimeError(f"No BOM daily rainfall rows found for station {station} in {START}..{END}")

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(selected[0].keys()))
        writer.writeheader()
        writer.writerows(selected)

    print(f"BOM displacement source: station {station}")
    print(f"Observed daily rows: {len(selected)}")
    print(f"Output: {OUTPUT}")
    print(f"Temporary archive URL resolved at runtime: {zip_url}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"BOM CDO displacement failed: {exc}", file=sys.stderr)
        raise
