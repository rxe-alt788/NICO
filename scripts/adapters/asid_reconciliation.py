from __future__ import annotations
import json
import urllib.request
from pathlib import Path
from typing import Any, Dict, List
from .common import csv_rows, first, json_load, read_source, safe_float


def _normalise(row: Dict[str, Any]) -> Dict[str, Any]:
    ts = first(row, 'timestamp', 'datetime', 'incident_datetime', 'date_time')
    date = first(row, 'date', 'incident_date', 'incident date')
    time = first(row, 'time', 'incident_time', 'incident time')
    if not ts and date:
        ts = f'{date} {time or "00:00"}'
    return {
        'id': str(first(row, 'id', 'incident_id', 'record_id', 'case number') or ''),
        'timestamp': ts,
        'location': first(row, 'location', 'beach', 'site', 'incident location'),
        'beachId': first(row, 'beach_id', 'beachid'),
        'eventClass': first(row, 'event_class', 'incident_type', 'type', 'incident category') or 'INCIDENT',
        'species': first(row, 'species', 'shark_species', 'shark species'),
        'speciesConfidence': first(row, 'species_confidence', 'species certainty', 'species confidence'),
        'latitude': safe_float(first(row, 'latitude', 'lat')),
        'longitude': safe_float(first(row, 'longitude', 'lon', 'lng')),
        'fatal': str(first(row, 'fatal', 'fatality') or '').lower() in ('1','true','yes','y'),
        'sourceRecord': first(row, 'source', 'source_record', 'reference'),
        'provenance': 'Taronga Australian Shark-Incident Database / DPI supplied import; record fields preserved where available'
    }


def _xlsx_rows(path: Path) -> List[Dict[str, Any]]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError('openpyxl is required to ingest the ASID XLSX release') from exc
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    iterator = ws.iter_rows(values_only=True)
    headers = [str(v).strip() if v is not None else '' for v in next(iterator)]
    rows = []
    for values in iterator:
        row = {headers[i]: values[i] for i in range(min(len(headers), len(values))) if headers[i]}
        if any(v not in (None, '') for v in row.values()):
            rows.append(row)
    return rows


def _download_binary(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={'User-Agent': '4NICO-pilot/0.6'})
    with urllib.request.urlopen(req, timeout=120) as response:
        dest.write_bytes(response.read())


def load(path: str | None, url: str | None) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    source = 'not_configured'
    rows: List[Dict[str, Any]] = []

    if path:
        p = Path(path)
        source = f'file:{p}'
        if not p.exists():
            return [], {'state': 'MISSING', 'source': source, 'note': 'Configured ASID file does not exist.'}
        if p.suffix.lower() in ('.xlsx', '.xlsm'):
            rows = _xlsx_rows(p)
        else:
            text = p.read_text(encoding='utf-8-sig')
            stripped = text.lstrip()
            raw = json_load(text) if stripped.startswith(('{','[')) else csv_rows(text)
            rows = raw.get('incidents', []) if isinstance(raw, dict) else raw
    elif url:
        source = url
        if '.xlsx' in url.lower() or '.xlsm' in url.lower():
            temp = Path('/tmp/4nico_asid_public.xlsx')
            _download_binary(url, temp)
            rows = _xlsx_rows(temp)
        else:
            text, _ = read_source(None, url)
            if text:
                stripped = text.lstrip()
                raw = json_load(text) if stripped.startswith(('{','[')) else csv_rows(text)
                rows = raw.get('incidents', []) if isinstance(raw, dict) else raw
    else:
        return [], {'state': 'MISSING', 'source': source, 'note': 'Supply Taronga ASID / DPI export. Public reporting is not silently substituted.'}

    incidents = [_normalise(r) for r in rows if isinstance(r, dict)]
    incidents = [i for i in incidents if i['timestamp'] or i['location']]
    return incidents, {'state': 'LOADED', 'source': source, 'count': len(incidents), 'sourceClass': 'AUTHORITATIVE_PUBLIC_RELEASE'}
