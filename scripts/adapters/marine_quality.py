from __future__ import annotations
import statistics
from collections import defaultdict
from typing import Any, Dict, List
from .common import csv_rows, first, nearest_hour, parse_ts, read_source, safe_float


def _truthy(value: Any) -> bool:
    return str(value or '').strip().lower() in ('1', 'true', 'yes', 'y')


def load(beachwatch_path: str | None, beachwatch_url: str | None, imos_path: str | None, imos_url: str | None, beach_ids: List[str]) -> tuple[Dict[str, Dict[Any, Dict[str, Any]]], Dict[str, Any]]:
    out: Dict[str, Dict[Any, Dict[str, Any]]] = defaultdict(dict)
    status: Dict[str, Any] = {}

    text, source = read_source(beachwatch_path, beachwatch_url)
    if text:
        rows = csv_rows(text); any_synthetic = False
        for row in rows:
            ts_raw = first(row, 'timestamp', 'sample_date', 'sample date', 'date')
            bid = str(first(row, 'beach_id', 'beachid', 'site_id') or '').strip()
            if not ts_raw or bid not in beach_ids:
                continue
            synthetic = _truthy(first(row, 'synthetic_flag', 'synthetic')); any_synthetic = any_synthetic or synthetic
            try: ts = nearest_hour(parse_ts(str(ts_raw)))
            except ValueError: continue
            out[bid].setdefault(ts, {}).update({
                'waterTempC': safe_float(first(row, 'water_temperature', 'water_temp_c', 'water temperature')),
                'conductivity': safe_float(first(row, 'conductivity')),
                'turbidityNtuBeachwatch': safe_float(first(row, 'turbidity_ntu', 'turbidity')),
                'enterococci': safe_float(first(row, 'enterococci', 'enterococci_cfu_100ml')),
                'beachwatchSyntheticFlag': synthetic
            })
        status['beachwatch'] = {
            'state': 'LOADED', 'source': source, 'rows': len(rows),
            'sourceClass': 'SYNTHETIC_ENGINEERING_FIXTURE' if any_synthetic else 'OBSERVED_ARCHIVE',
            'synthetic': any_synthetic,
            'note': 'Beachwatch historical exports commonly include enterococci, water temperature and conductivity; turbidity is used only when explicitly present.'
        }
    else:
        status['beachwatch'] = {'state': 'MISSING', 'source': source, 'note': 'Supply Beachwatch historical water-quality export.'}

    text, source = read_source(imos_path, imos_url)
    if text:
        rows = csv_rows(text); parsed = []; sst: Dict[str, List[float]] = defaultdict(list); any_synthetic = False
        for row in rows:
            ts_raw = first(row, 'timestamp', 'datetime', 'time')
            bid = str(first(row, 'beach_id', 'beachid') or '').strip()
            if not ts_raw or bid not in beach_ids: continue
            synthetic = _truthy(first(row, 'synthetic_flag', 'synthetic')); any_synthetic = any_synthetic or synthetic
            try: ts = nearest_hour(parse_ts(str(ts_raw)))
            except ValueError: continue
            value = safe_float(first(row, 'sst_c', 'sst', 'sst_celsius', 'sea_surface_temperature'))
            up = safe_float(first(row, 'upwelling_index', 'upwelling'))
            acoustic = safe_float(first(row, 'acoustic_density_pct', 'seasonal_acoustic_density_pct'))
            parsed.append((bid, ts, value, up, acoustic, synthetic))
            if value is not None: sst[bid].append(value)
        for bid, ts, value, up, acoustic, synthetic in parsed:
            baseline = statistics.median(sst[bid]) if sst[bid] else None
            anomaly = None if value is None or baseline is None else round(value - baseline, 3)
            out[bid].setdefault(ts, {}).update({
                'sstC': value, 'sstAnomaly': anomaly, 'upwellingIndex': up,
                'seasonalAcousticDensityPct': acoustic, 'marineSyntheticFlag': synthetic
            })
        status['imos'] = {
            'state': 'LOADED', 'source': source, 'rows': len(rows),
            'sourceClass': 'SYNTHETIC_ENGINEERING_FIXTURE' if any_synthetic else 'OBSERVED_ARCHIVE',
            'synthetic': any_synthetic,
            'note': 'Pilot SST anomaly uses supplied-window median pending climatological baseline.'
        }
    else:
        status['imos'] = {'state': 'MISSING', 'source': source, 'note': 'Supply IMOS/BOM marine point extraction for the six pilot sites.'}

    return out, status
