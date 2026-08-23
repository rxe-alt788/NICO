#!/usr/bin/env python3
"""Build data/empirical_18m_series.json from source-specific adapters.

No synthetic environmental value is inserted. A field absent upstream remains absent.
"""
from __future__ import annotations
import argparse, json, os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from adapters import bom_archive, waternsw_api, marine_quality, asid_reconciliation

ROOT = Path(__file__).resolve().parents[1]
START = datetime.fromisoformat('2025-02-23T00:00:00+11:00')
END = datetime.fromisoformat('2026-08-23T23:59:59+10:00')


def load_beaches():
    data = json.loads((ROOT / 'data/pilot_beaches.json').read_text(encoding='utf-8'))
    return data['beaches']


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

    rain, status['bom'] = bom_archive.load(os.getenv('BOM_ARCHIVE_CSV'), os.getenv('BOM_ARCHIVE_URL'), beach_ids)
    water, status['waternsw'] = waternsw_api.load(os.getenv('WATERNSW_ARCHIVE_CSV'), os.getenv('WATERNSW_ARCHIVE_URL'), beach_ids)
    marine, marine_status = marine_quality.load(
        os.getenv('BEACHWATCH_ARCHIVE_CSV'), os.getenv('BEACHWATCH_ARCHIVE_URL'),
        os.getenv('IMOS_ARCHIVE_CSV'), os.getenv('IMOS_ARCHIVE_URL'), beach_ids
    )
    status.update(marine_status)
    incidents, status['incidents'] = asid_reconciliation.load(
        os.getenv('ASID_ARCHIVE_FILE') or os.getenv('DPI_INCIDENTS_JSON'),
        os.getenv('ASID_ARCHIVE_URL') or os.getenv('DPI_INCIDENTS_URL')
    )

    empirical = merge_layers(beach_ids, rain, water, marine)
    loaded = [k for k,v in status.items() if v.get('state') == 'LOADED']
    coverage = {bid: len(empirical[bid]) for bid in beach_ids}
    payload = {
        'schemaVersion': '0.5.0',
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'evaluationWindow': {'start': START.isoformat(), 'end': END.isoformat()},
        'mode': 'EMPIRICAL_PARTIAL' if loaded else 'AWAITING_ARCHIVES',
        'qualityRule': 'Null/absent means unavailable. Missing environmental values never default to GREEN.',
        'sourceStatus': status,
        'coverageHoursByBeach': coverage,
        'incidents': incidents,
        'beaches': empirical
    }
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(out), 'mode': payload['mode'], 'loadedSources': loaded, 'coverageHoursByBeach': coverage}, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
