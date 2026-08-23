from __future__ import annotations
from collections import defaultdict, deque
from datetime import timedelta
from typing import Any, Dict, List
from .common import csv_rows, first, nearest_hour, parse_ts, percentile_rank, read_source, safe_float


def _truthy(value: Any) -> bool:
    return str(value or '').strip().lower() in ('1', 'true', 'yes', 'y')


def load(path: str | None, url: str | None, beach_ids: List[str]) -> tuple[Dict[str, Dict[Any, Dict[str, Any]]], Dict[str, Any]]:
    text, source = read_source(path, url)
    out: Dict[str, Dict[Any, Dict[str, Any]]] = defaultdict(dict)
    if not text:
        return out, {'state': 'MISSING', 'source': source, 'note': 'Supply BOM Climate Data Online daily/hourly CSV export. Free CDO downloads exist, but extraction/download URLs are not durable.'}
    rows = csv_rows(text)
    points: Dict[str, List[tuple[Any, float, bool]]] = defaultdict(list)
    any_synthetic = False
    for row in rows:
        ts_raw = first(row, 'timestamp', 'datetime', 'date_time', 'local date time', 'date')
        rain = safe_float(first(row, 'rainfall_mm', 'rain_mm', 'rainfall', 'rainfall amount (millimetres)', 'rainfall amount'))
        if not ts_raw or rain is None:
            continue
        bid = str(first(row, 'beach_id', 'beachid') or 'all').strip()
        synthetic = _truthy(first(row, 'synthetic_flag', 'synthetic'))
        any_synthetic = any_synthetic or synthetic
        try:
            points[bid].append((parse_ts(str(ts_raw)), rain, synthetic))
        except ValueError:
            continue

    for bid in beach_ids:
        src = points.get(bid) or points.get('all') or []
        q: deque[tuple[Any, float, bool]] = deque(); total = 0.0; synthetic_window = 0; sums: List[tuple[Any, float, bool]] = []
        for ts, value, synthetic in sorted(src):
            q.append((ts, value, synthetic)); total += value; synthetic_window += int(synthetic)
            cutoff = ts - timedelta(hours=72)
            while q and q[0][0] <= cutoff:
                _, old, old_syn = q.popleft(); total -= old; synthetic_window -= int(old_syn)
            sums.append((nearest_hour(ts), round(total, 3), synthetic_window > 0))
        dist = [v for _, v, _ in sums]
        for ts, value, synthetic in sums:
            out[bid].setdefault(ts, {}).update({'rain72hMm': value, 'rainPct': percentile_rank(dist, value), 'rainSyntheticFlag': synthetic})
    return out, {
        'state': 'LOADED', 'source': source, 'rows': len(rows),
        'sourceClass': 'SYNTHETIC_ENGINEERING_FIXTURE' if any_synthetic else 'OBSERVED_ARCHIVE',
        'synthetic': any_synthetic,
        'note': '72h rolling accumulation calculated from supplied observations. Daily inputs are accepted but reduce temporal precision.'
    }
