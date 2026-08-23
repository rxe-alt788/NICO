from __future__ import annotations
from typing import Any, Dict, List
from .common import csv_rows, first, json_load, read_source, safe_float


def _normalise(row: Dict[str, Any]) -> Dict[str, Any]:
    ts = first(row, 'timestamp', 'datetime', 'incident_datetime', 'date_time')
    date = first(row, 'date', 'incident_date')
    time = first(row, 'time', 'incident_time')
    if not ts and date:
        ts = f'{date} {time or "00:00"}'
    return {
        'id': str(first(row, 'id', 'incident_id', 'record_id') or ''),
        'timestamp': ts,
        'location': first(row, 'location', 'beach', 'site'),
        'beachId': first(row, 'beach_id', 'beachid'),
        'eventClass': first(row, 'event_class', 'incident_type', 'type') or 'INCIDENT',
        'species': first(row, 'species', 'shark_species'),
        'speciesConfidence': first(row, 'species_confidence', 'species certainty'),
        'latitude': safe_float(first(row, 'latitude', 'lat')),
        'longitude': safe_float(first(row, 'longitude', 'lon', 'lng')),
        'fatal': str(first(row, 'fatal', 'fatality') or '').lower() in ('1','true','yes','y'),
        'sourceRecord': first(row, 'source', 'source_record', 'reference'),
        'provenance': 'ASID/DPI supplied import; authoritative status depends on source file supplied to adapter'
    }


def load(path: str | None, url: str | None) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    text, source = read_source(path, url)
    if not text:
        return [], {'state': 'MISSING', 'source': source, 'note': 'Supply Taronga ASID / DPI export or API response. Public reporting is not silently substituted.'}
    stripped = text.lstrip()
    if stripped.startswith('{') or stripped.startswith('['):
        raw = json_load(text)
        rows = raw.get('incidents', []) if isinstance(raw, dict) else raw
    else:
        rows = csv_rows(text)
    incidents = [_normalise(r) for r in rows if isinstance(r, dict)]
    incidents = [i for i in incidents if i['timestamp'] or i['location']]
    return incidents, {'state': 'LOADED', 'source': source, 'count': len(incidents)}
