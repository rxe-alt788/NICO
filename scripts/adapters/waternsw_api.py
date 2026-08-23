from __future__ import annotations
import os
from collections import defaultdict
from typing import Any, Dict, List
from .common import csv_rows, first, nearest_hour, parse_ts, percentile_rank, read_source, safe_float


def _truthy(value: Any) -> bool:
    return str(value or '').strip().lower() in ('1', 'true', 'yes', 'y')


def load(path: str | None, url: str | None, beach_ids: List[str], subscription_key: str | None = None) -> tuple[Dict[str, Dict[Any, Dict[str, Any]]], Dict[str, Any]]:
    headers = {}
    key = subscription_key or os.getenv('WATERNSW_SUBSCRIPTION_KEY')
    if key:
        headers['Ocp-Apim-Subscription-Key'] = key
    text, source = read_source(path, url, headers)
    out: Dict[str, Dict[Any, Dict[str, Any]]] = defaultdict(dict)
    if not text:
        return out, {'state': 'MISSING', 'source': source, 'note': 'Supply WaterInsights/WaterNSW 15-minute export or a configured keyed API URL.'}
    rows = csv_rows(text)
    parsed = []
    turbidity: Dict[str, List[float]] = defaultdict(list)
    any_synthetic = False
    for row in rows:
        ts_raw = first(row, 'timestamp', 'datetime', 'time', 'date time', 'sample time')
        if not ts_raw:
            continue
        bid = str(first(row, 'beach_id', 'beachid') or 'all').strip()
        turb = safe_float(first(row, 'turbidity_ntu', 'turbidity', 'ntu'))
        discharge = safe_float(first(row, 'discharge_m3s', 'flow_m3s', 'discharge', 'flow'))
        synthetic = _truthy(first(row, 'synthetic_flag', 'synthetic'))
        any_synthetic = any_synthetic or synthetic
        try:
            ts = nearest_hour(parse_ts(str(ts_raw)))
        except ValueError:
            continue
        parsed.append((bid, ts, turb, discharge, synthetic))
        if turb is not None:
            turbidity[bid].append(turb)
    for bid, ts, turb, discharge, synthetic in parsed:
        targets = beach_ids if bid == 'all' else [bid]
        for target in targets:
            if target not in beach_ids:
                continue
            dist = turbidity.get(bid, [])
            out[target].setdefault(ts, {}).update({
                'turbidityNtu': turb,
                'turbidityPct': percentile_rank(dist, turb),
                'dischargeM3s': discharge,
                'waterSyntheticFlag': synthetic
            })
    return out, {
        'state': 'LOADED', 'source': source, 'rows': len(rows),
        'auth': 'subscription-key' if key else 'file/export',
        'sourceClass': 'SYNTHETIC_ENGINEERING_FIXTURE' if any_synthetic else 'OBSERVED_ARCHIVE',
        'synthetic': any_synthetic
    }
