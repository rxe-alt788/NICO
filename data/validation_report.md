# 4NICO Validation Report

Generated from `empirical_18m_series.json`. Dataset mode: **AWAITING_ARCHIVES**.

> Synthetic environmental fixtures are engineering test data. They are excluded from empirical performance claims.

## Source coverage

- **bom**: MISSING · UNCLASSIFIED — Supply BOM Climate Data Online daily/hourly CSV export. Free CDO downloads exist, but extraction/download URLs are not durable.
- **waternsw**: MISSING · UNCLASSIFIED — Supply WaterInsights/WaterNSW 15-minute export or a configured keyed API URL.
- **beachwatch**: MISSING · UNCLASSIFIED — Supply Beachwatch historical water-quality export.
- **imos**: MISSING · UNCLASSIFIED — Supply IMOS/BOM marine point extraction for the six pilot sites.
- **incidents**: MISSING · UNCLASSIFIED — Supply Taronga ASID / DPI export. Public reporting is not silently substituted.

## Empirical-only results

| Beach | Classified hours | Incomplete | Synthetic excluded | Green | Orange | Red | Raw transitions/mo | 24h-hold transitions/mo | False-alert burden | True-negative rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| palm-beach | 0 | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| north-steyne | 0 | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| bondi | 0 | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| coogee | 0 | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| cronulla | 0 | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| balmoral | 0 | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Engineering fixture results

| Beach | Classified hours | Incomplete | Synthetic excluded | Green | Orange | Red | Raw transitions/mo | 24h-hold transitions/mo | False-alert burden | True-negative rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| palm-beach | 0 | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| north-steyne | 0 | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| bondi | 0 | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| coogee | 0 | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| cronulla | 0 | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| balmoral | 0 | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Empirical lead time

- Not calculable from authoritative environmental observations yet.

## Clear-water secondary-cue test

- No complete fixture series available for ON/OFF comparison.

## Validation gate

**EMPIRICAL VALIDATION REMAINS BLOCKED.** Synthetic fixture coverage proves ingestion/rules/hysteresis execution only; it does not establish shark-risk discrimination, lead time, or false-alert performance.

Missing observations are never interpreted as GREEN. `INSUFFICIENT_ENV_DATA` is a data-quality state, not a low-risk state.
