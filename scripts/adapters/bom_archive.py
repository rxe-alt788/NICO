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
    points: Dict[str, List[tuple[Any, float, bool, str]]] = defaultdict(list)
    any_synthetic = False
    daily_input = False
    source_classes = set()
    station_ids = set()

    for row in rows:
        ts_raw = first(row, 'timestamp', 'datetime', 'date_time', 'local date time', 'date')
        rain = safe_float(first(row, 'rainfall_mm', 'rain_mm', 'rainfall', 'rainfall amount (millimetres)', 'rainfall amount'))
        if not ts_raw or rain is None:
            continue
        bid = str(first(row, 'beach_id', 'beachid') or 'all').strip()
        synthetic = _truthy(first(row, 'synthetic_flag', 'synthetic'))
        resolution = str(first(row, 'observation_resolution', 'resolution') or '').strip().lower()
        source_class = str(first(row, 'source_class') or '').strip()
        station_id = str(first(row, 'station_id', 'station') or '').strip()
        any_synthetic = any_synthetic or synthetic
        daily_input = daily_input or resolution == 'daily'
        if source_class:
            source_classes.add(source_class)
        if station_id:
            station_ids.add(station_id)
        try:
            points[bid].append((parse_ts(str(ts_raw)), rain, synthetic, resolution))
        except ValueError:
            continue

    for bid in beach_ids:
        src = points.get(bid) or points.get('all') or []
        q: deque[tuple[Any, float, bool]] = deque()
        total = 0.0
        synthetic_window = 0
        sums: List[tuple[Any, float, bool, str]] = []
        for ts, value, synthetic, resolution in sorted(src):
            q.append((ts, value, synthetic))
            total += value
            synthetic_window += int(synthetic)
            cutoff = ts - timedelta(hours=72)
            while q and q[0][0] <= cutoff:
                _, old, old_syn = q.popleft()
                total -= old
                synthetic_window -= int(old_syn)
            sums.append((nearest_hour(ts), round(total, 3), synthetic_window > 0, resolution))

        dist = [v for _, v, _, _ in sums]
        for idx, (ts, value, synthetic, resolution) in enumerate(sums):
            pct = percentile_rank(dist, value)
            fields = {
                'rain72hMm': value,
                'rainPct': pct,
                'rainSyntheticFlag': synthetic,
                'rainObservationResolution': resolution or 'unknown'
            }
            if resolution == 'daily':
                # Daily rainfall is observed once per day. Hold the derived 72h
                # state until the next daily observation so hourly validation can
                # combine it with higher-frequency marine/hydrometric fields without
                # fabricating additional rainfall measurements.
                next_ts = sums[idx + 1][0] if idx + 1 < len(sums) else ts + timedelta(hours=24)
                cursor = ts
                while cursor < next_ts and cursor < ts + timedelta(hours=24):
                    out[bid].setdefault(cursor, {}).update(fields)
                    cursor += timedelta(hours=1)
            else:
                out[bid].setdefault(ts, {}).update(fields)

    source_class = 'SYNTHETIC_ENGINEERING_FIXTURE' if any_synthetic else (
        next(iter(source_classes)) if len(source_classes) == 1 else 'OBSERVED_ARCHIVE'
    )
    return out, {
        'state': 'LOADED',
        'source': source,
        'rows': len(rows),
        'sourceClass': source_class,
        'synthetic': any_synthetic,
        'stations': sorted(station_ids),
        'dailyInputExpandedHourly': daily_input,
        'note': '72h rolling accumulation calculated from supplied observations. Daily inputs are held between observations for hourly state alignment; this does not create new rainfall measurements.'
    }
