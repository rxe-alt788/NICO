#!/usr/bin/env python3
"""Bootstrap 4NICO raw inputs for end-to-end engineering validation.

Downloads the public Taronga Australian Shark-Incident Database release from
Zenodo and generates deterministic *synthetic* environmental fixtures where
restricted/curated historical telemetry is not yet available.

Synthetic files are engineering fixtures only. Every generated row includes
synthetic_flag=true and source_class=SYNTHETIC_ENGINEERING_FIXTURE so downstream
validation cannot mistake pipeline coverage for empirical evidence.
"""
from __future__ import annotations

import csv
import math
import random
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

ASID_URL = "https://zenodo.org/records/18752301/files/Australian%20Shark-Incident%20Database%20Public%20Version.xlsx?download=1"
ASID_DEST = RAW / "asid_public.xlsx"

BEACHES = {
    "palm-beach": "Palm Beach",
    "north-steyne": "North Steyne",
    "bondi": "Bondi",
    "coogee": "Coogee",
    "cronulla": "Cronulla",
    "balmoral": "Balmoral",
}
START = datetime(2020, 1, 1, 0, 0)
END = datetime(2026, 8, 20, 23, 0)


def daterange_hours(start: datetime, end: datetime):
    current = start
    while current <= end:
        yield current
        current += timedelta(hours=1)


def fetch_asid() -> None:
    print("Fetching ASID dataset from Zenodo...")
    req = urllib.request.Request(ASID_URL, headers={"User-Agent": "4NICO-pilot/0.6"})
    try:
        with urllib.request.urlopen(req, timeout=120) as response, ASID_DEST.open("wb") as out:
            out.write(response.read())
        print(f"ASID dataset downloaded: {ASID_DEST}")
    except Exception as exc:
        print(f"ASID download failed: {exc}")
        # Deliberately do not create a placeholder XLSX. The ASID adapter must
        # report MISSING rather than ingesting a counterfeit authoritative file.


def generate_environmental_fixtures() -> None:
    print("Generating deterministic synthetic environmental fixtures...")
    rng = random.Random(42)
    dates = list(daterange_hours(START, END))

    # Shared synthetic rain driver, emitted through the BOM adapter contract.
    rainfall = []
    turbidity = []
    current_turb = 2.0
    for _ in dates:
        r = rng.expovariate(1 / 0.5)
        if r < 0.8:
            r = 0.0
        rainfall.append(r)
        current_turb = max(1.5, current_turb * 0.95 + r * 1.8 + rng.gauss(0, 0.1))
        turbidity.append(current_turb)

    with (RAW / "bom_rainfall_history.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "beach_id", "rainfall_mm", "synthetic_flag", "source_class"])
        w.writeheader()
        for ts, rain in zip(dates, rainfall):
            for bid in BEACHES:
                w.writerow({
                    "timestamp": ts.isoformat(sep=" "), "beach_id": bid,
                    "rainfall_mm": round(rain, 4), "synthetic_flag": "true",
                    "source_class": "SYNTHETIC_ENGINEERING_FIXTURE"
                })

    with (RAW / "waternsw_history.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "beach_id", "station_id", "turbidity_ntu", "discharge_m3s", "synthetic_flag", "source_class"])
        w.writeheader()
        for ts, turb, rain in zip(dates, turbidity, rainfall):
            discharge = max(0.2, 2.5 + rain * 6.0 + rng.gauss(0, 0.25))
            for bid in BEACHES:
                w.writerow({
                    "timestamp": ts.isoformat(sep=" "), "beach_id": bid,
                    "station_id": "WATERNSW_SYD_ESTUARY_FIXTURE",
                    "turbidity_ntu": round(turb, 2), "discharge_m3s": round(discharge, 2),
                    "synthetic_flag": "true", "source_class": "SYNTHETIC_ENGINEERING_FIXTURE"
                })

    with (RAW / "imos_sst_history.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "beach_id", "station_id", "sst_c", "upwelling_index", "acoustic_density_pct", "synthetic_flag", "source_class"])
        w.writeheader()
        for ts in dates:
            doy = ts.timetuple().tm_yday
            sst = 19.5 + 3.5 * math.sin(2 * math.pi * (doy - 60) / 365.0) + rng.gauss(0, 0.3)
            upwelling = 0.9 * math.sin(2 * math.pi * doy / 45.0) + rng.gauss(0, 0.25)
            acoustic = min(1.0, max(0.0, 0.35 + 0.2 * math.sin(2 * math.pi * (doy - 20) / 365.0) + rng.gauss(0, 0.08)))
            for bid in BEACHES:
                w.writerow({
                    "timestamp": ts.isoformat(sep=" "), "beach_id": bid,
                    "station_id": "IMOS_SYD_OFFSHORE_FIXTURE", "sst_c": round(sst, 2),
                    "upwelling_index": round(upwelling, 3), "acoustic_density_pct": round(acoustic, 3),
                    "synthetic_flag": "true", "source_class": "SYNTHETIC_ENGINEERING_FIXTURE"
                })

    with (RAW / "beachwatch_history.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "beach_id", "site", "enterococci", "water_temp_c", "synthetic_flag", "source_class"])
        w.writeheader()
        day = START
        while day.date() <= END.date():
            doy = day.timetuple().tm_yday
            water_temp = 19.5 + 3.5 * math.sin(2 * math.pi * (doy - 60) / 365.0)
            for bid, site in BEACHES.items():
                # deterministic lognormal-style fixture using exp(normal)
                enterococci = int(math.exp(rng.gauss(2.0, 1.0)))
                w.writerow({
                    "date": day.date().isoformat(), "beach_id": bid, "site": site,
                    "enterococci": enterococci, "water_temp_c": round(water_temp, 1),
                    "synthetic_flag": "true", "source_class": "SYNTHETIC_ENGINEERING_FIXTURE"
                })
            day += timedelta(days=1)

    print(f"Synthetic fixture files written under {RAW}")


def main() -> int:
    fetch_asid()
    generate_environmental_fixtures()
    print("Raw data bootstrap complete. Synthetic lineage is explicit in every proxy row.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
