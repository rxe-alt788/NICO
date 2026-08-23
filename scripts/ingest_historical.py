#!/usr/bin/env python3
"""Build data/empirical_18m_series.json from source-specific adapters.

Observed/archive inputs and synthetic engineering fixtures may coexist, but lineage is
preserved. Any synthetic environmental source forces dataset mode HYBRID_FIXTURE;
synthetic coverage must not be represented as empirical validation evidence.
"""
from __future__ import annotations
import argparse, json, os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from adapters import bom_archive, waternsw_api, marine_quality, asid_reconciliation

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
START = datetime.fromisoformat('2025-02-23T00:00:00+11:00')
END = datetime.fromisoformat('2026-08-23T23:59:59+10:00')


def load_beaches():
    data = json.loads((ROOT / 'data/pilot_beaches.json').read_text(encoding='utf-8'))
    return data['beaches']


def first_existing(*paths: Path) -> str | None:
    for p in paths:
        if p.exists():
            return str(p)
    return None


def merge_layers(beach_ids, *layers):
    merged = defaultdict(dict)
    start_utc, end_utc = START.astimezone(timezone.utc), END.astimezone(timezone.utc)
    for layer in layers:
        for bid, points in layer.items():
            if bid not in beach_ids:
                continue
            for ts, fields in points.items():
                if start_utc <= ts <= end_utc:
                    merged[bid].setdefault(ts, {}).update({k: v for k, v in fields.items() if v is not None})
    return {
        bid: [{'timestamp': ts.isoformat().replace('+00:00','Z'), **fields} for ts, fields in sorted(merged[bid].items())]
        for bid in beach_ids
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', default=str(ROOT / 'data/empirical_18m_series.json'))
    args = ap.parse_args()
    beaches = load_beaches(); beach_ids = [b['id'] for b in beaches]
    status = {}

    bom_path = os.getenv('BOM_ARCHIVE_CSV') or first_existing(RAW/'bom_rainfall_history.csv', RAW/'bom_rainfall.csv')
    water_path = os.getenv('WATERNSW_ARCHIVE_CSV') or first_existing(RAW/'waternsw_history.csv', RAW/'waternsw_hydrometric.csv')
    beachwatch_path = os.getenv('BEACHWATCH_ARCHIVE_CSV') or first_existing(RAW/'beachwatch_history.csv', RAW/'beachwatch.csv')
    imos_path = os.getenv('IMOS_ARCHIVE_CSV') or first_existing(RAW/'imos_sst_history.csv', RAW/'imos_marine.csv')
    asid_path = os.getenv('ASID_ARCHIVE_FILE') or os.getenv('DPI_INCIDENTS_JSON') or first_existing(RAW/'asid_public.xlsx', RAW/'asid_incidents.xlsx', RAW/'asid_incidents.csv', RAW/'asid_incidents.json')
    interim_path = os.getenv('INCIDENT_INTERIM_FILE') or str(ROOT/'data/incidents_interim.json')

    rain, status['bom'] = bom_archive.load(bom_path, os.getenv('BOM_ARCHIVE_URL'), beach_ids)
    water, status['waternsw'] = waternsw_api.load(water_path, os.getenv('WATERNSW_ARCHIVE_URL'), beach_ids)
    marine, marine_status = marine_quality.load(
        beachwatch_path, os.getenv('BEACHWATCH_ARCHIVE_URL'),
        imos_path, os.getenv('IMOS_ARCHIVE_URL'), beach_ids
    )
    status.update(marine_status)
    incidents, status['incidents'] = asid_reconciliation.load(
        asid_path,
        os.getenv('ASID_ARCHIVE_URL') or os.getenv('DPI_INCIDENTS_URL'),
        interim_path
    )

    merged = merge_layers(beach_ids, rain, water, marine)
    loaded = [k for k,v in status.items() if v.get('state') in ('LOADED','INTERIM_ONLY')]
    synthetic_sources = [k for k,v in status.items() if v.get('synthetic')]
    coverage = {bid: len(merged[bid]) for bid in beach_ids}
    if synthetic_sources:
        mode = 'HYBRID_FIXTURE'
    elif loaded:
        mode = 'EMPIRICAL_PARTIAL'
    else:
        mode = 'AWAITING_ARCHIVES'

    payload = {
        'schemaVersion': '0.7.0',
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'evaluationWindow': {'start': START.isoformat(), 'end': END.isoformat()},
        'mode': mode,
        'qualityRule': 'Null/absent means unavailable. Missing environmental values never default to GREEN. Synthetic fixtures are excluded from empirical claims.',
        'incidentValidationRule': 'ASID_AUTHORITATIVE and VERIFIED_INTERIM are validation-eligible. UNVERIFIED_SUPPLEMENTARY is excluded from metrics.',
        'sourceStatus': status,
        'syntheticEnvironmentalSources': synthetic_sources,
        'coverageHoursByBeach': coverage,
        'incidents': incidents,
        'beaches': merged
    }
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(out), 'mode': mode, 'loadedSources': loaded, 'syntheticSources': synthetic_sources, 'coverageHoursByBeach': coverage}, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
