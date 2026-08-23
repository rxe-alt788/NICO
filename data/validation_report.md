# 4NICO Empirical Validation Baseline

Generated from `empirical_18m_series.json`. Dataset mode: **AWAITING_ARCHIVES**.

## Source coverage

- **bom**: MISSING — Supply BOM Climate Data Online daily/hourly CSV export. Free CDO downloads exist, but extraction/download URLs are not durable.
- **waternsw**: MISSING — Supply WaterInsights/WaterNSW 15-minute export or a configured keyed API URL.
- **beachwatch**: MISSING — Supply Beachwatch historical water-quality export.
- **imos**: MISSING — Supply IMOS/BOM marine point extraction for the six pilot sites.
- **incidents**: MISSING — Supply Taronga ASID / DPI export. Public reporting is not silently substituted.

## Core empirical results

| Beach | Complete classified hours | Incomplete hours | Green | Orange | Red | Raw transitions/mo | 24h-hold transitions/mo | False-alert burden | True-negative rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| palm-beach | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| north-steyne | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| bondi | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| coogee | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| cronulla | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| balmoral | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Empirical lead time

- Not calculable: no incident has a complete 72-hour empirical pre-event series in the hydrated dataset.

## Clear-water secondary-cue comparison

- Not calculable until complete core environmental observations plus upwelling/acoustic cue fields are available.

## Validation gate

**BLOCKED BY SOURCE COVERAGE.** The pipeline is functioning fail-closed: zero empirical hours are classifiable, so no flag distribution, false-alert, lead-time, or signal-stability claim is made.

Missing observations are never interpreted as GREEN. `INSUFFICIENT_ENV_DATA` is a data-quality state, not a low-risk state.
