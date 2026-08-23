# 4NICO Empirical Validation Baseline

Generated against `data/empirical_18m_series.json` after the historical-adapter refactor.

Dataset mode: **AWAITING_ARCHIVES**

## Source coverage

- **BOM**: MISSING. Historical daily/hourly CSV export not yet supplied.
- **WaterNSW**: MISSING. WaterInsights export or keyed API source not yet configured.
- **Beachwatch**: MISSING. Historical water-quality export not yet supplied.
- **IMOS/BOM marine**: MISSING. Pilot-site SST/upwelling point extraction not yet supplied.
- **Taronga ASID / DPI incidents**: MISSING. Authoritative incident export not yet supplied; public-report seeds are no longer treated as empirical records.

## Core empirical results

| Beach | Complete classified hours | Incomplete hours | Green | Orange | Red | Raw transitions/month | 24h-hold transitions/month | False-alert burden | True-negative rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Palm Beach | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| North Steyne | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Bondi | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Coogee | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Cronulla | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Balmoral | 0 | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Empirical lead time

Not calculable. No 2026 incident currently has an authoritative incident record plus a complete 72-hour empirical pre-event environmental series in the hydrated dataset.

## Signal stability

Not calculable. The 24-hour de-escalation hysteresis implementation is ready, but there are no complete empirical hourly observations on which to compare raw versus stabilised transition frequency.

## Clear-water secondary-cue comparison

Not calculable. The provisional upwelling and seasonal acoustic-density module remains disabled by default. A valid ON/OFF comparison requires complete core environmental observations plus the secondary cue fields around Coogee and non-incident control periods.

## Validation gate

**BLOCKED BY SOURCE COVERAGE.**

This is the correct fail-closed result for the first empirical ingestion pass. Zero empirical hours are currently classifiable, so the project makes no flag-distribution, false-alert, lead-time, sensitivity, specificity, or signal-stability claim from the historical dataset.

Missing observations are never interpreted as GREEN. `INSUFFICIENT_ENV_DATA` is a data-quality state, not a low-risk state.

## Immediate data acquisition gate

1. Export or request BOM historical rainfall observations mapped to the six pilot beaches/catchments.
2. Configure WaterNSW Water Data API credentials or supply 15-minute WaterInsights exports for Hawkesbury, Georges and relevant Sydney coastal catchments.
3. Export Beachwatch historical water-quality observations and explicitly identify whether any turbidity/clarity field exists for each pilot site.
4. Produce IMOS/BOM marine point extractions for SST and the proposed upwelling metric at each pilot beach.
5. Obtain/reconcile the 2026 Taronga ASID / NSW DPI incident records with timestamps, species confidence and coordinates.
6. Re-run `python scripts/ingest_historical.py` followed by `python scripts/run_validation.py`.

The next valid milestone is not a prettier chart. It is the first non-zero `coverageHoursByBeach` value with provenance sufficient for DPI to reproduce.
