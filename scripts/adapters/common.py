from __future__ import annotations
import csv, io, json, math, os, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

UTC = timezone.utc
SYDNEY_STANDARD = timezone(timedelta(hours=10))


def safe_float(v: Any) -> Optional[float]:
    if v in (None, '', 'NA', 'N/A', 'null', 'None', '-'):
        return None
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def parse_ts(value: str) -> datetime:
    value = value.strip().replace('Z', '+00:00')
    for fmt in (None, '%d/%m/%Y %H:%M', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            dt = datetime.fromisoformat(value) if fmt is None else datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=SYDNEY_STANDARD)
            return dt
        except ValueError:
            pass
    raise ValueError(f'Unparseable timestamp: {value}')


def nearest_hour(dt: datetime) -> datetime:
    dt = dt.astimezone(UTC)
    out = dt.replace(minute=0, second=0, microsecond=0)
    if dt.minute >= 30:
        out += timedelta(hours=1)
    return out


def fetch_text(url: str, headers: Optional[Dict[str, str]] = None) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': '4NICO-pilot/0.5', **(headers or {})})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode('utf-8-sig')


def read_source(path: Optional[str] = None, url: Optional[str] = None, headers: Optional[Dict[str, str]] = None) -> tuple[Optional[str], str]:
    if path:
        p = Path(path)
        if not p.exists():
            return None, f'missing_file:{p}'
        return p.read_text(encoding='utf-8-sig'), f'file:{p}'
    if url:
        return fetch_text(url, headers), url
    return None, 'not_configured'


def csv_rows(text: str) -> List[Dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def json_load(text: str) -> Any:
    return json.loads(text)


def first(row: Dict[str, Any], *keys: str) -> Any:
    lowered = {str(k).strip().lower(): v for k, v in row.items()}
    for key in keys:
        if key.lower() in lowered and lowered[key.lower()] not in (None, ''):
            return lowered[key.lower()]
    return None


def percentile_rank(values: List[float], value: Optional[float]) -> Optional[float]:
    if value is None or not values:
        return None
    ordered = sorted(values)
    return sum(1 for x in ordered if x <= value) / len(ordered)
