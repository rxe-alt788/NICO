# 4NICO Validation Report

Generated from `empirical_18m_series.json`. Dataset mode: **HYBRID_FIXTURE**.

> Synthetic environmental fixtures are engineering test data. They are excluded from empirical performance claims.

## Source coverage

- **bom**: LOADED · SYNTHETIC_ENGINEERING_FIXTURE — 72h rolling accumulation calculated from supplied observations. Daily inputs are accepted but reduce temporal precision.
- **waternsw**: LOADED · SYNTHETIC_ENGINEERING_FIXTURE — file:data/raw/waternsw_history.csv
- **beachwatch**: LOADED · SYNTHETIC_ENGINEERING_FIXTURE — Beachwatch historical exports commonly include enterococci, water temperature and conductivity; turbidity is used only when explicitly present.
- **imos**: LOADED · SYNTHETIC_ENGINEERING_FIXTURE — Pilot SST anomaly uses supplied-window median pending climatological baseline.
- **incidents**: LOADED · AUTHORITATIVE_PUBLIC_RELEASE — ASID public fields ingested as published. Month/year-only records are not promoted to exact timestamps; post-release 2026 incidents require a newer DPI/ASID source.

## Empirical-only results

| Beach | Classified hours | Incomplete | Synthetic excluded | Green | Orange | Red | Raw transitions/mo | 24h-hold transitions/mo | False-alert burden | True-negative rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| palm-beach | 0 | 0 | 13128 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| north-steyne | 0 | 0 | 13128 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| bondi | 0 | 0 | 13128 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| coogee | 0 | 0 | 13128 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| cronulla | 0 | 0 | 13128 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| balmoral | 0 | 0 | 13128 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Engineering fixture results

| Beach | Classified hours | Incomplete | Synthetic excluded | Green | Orange | Red | Raw transitions/mo | 24h-hold transitions/mo | False-alert burden | True-negative rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| palm-beach | 13128 | 0 | 0 | 31.0% | 16.9% | 52.0% | 89.83 | 12.83 | 80.5% | 19.5% |
| north-steyne | 13128 | 0 | 0 | 31.0% | 16.9% | 52.0% | 89.83 | 12.83 | 80.5% | 19.5% |
| bondi | 13128 | 0 | 0 | 31.0% | 16.9% | 52.0% | 89.83 | 12.83 | 80.5% | 19.5% |
| coogee | 13128 | 0 | 0 | 31.0% | 16.9% | 52.0% | 89.83 | 12.83 | 80.5% | 19.5% |
| cronulla | 13128 | 0 | 0 | 31.0% | 16.9% | 52.0% | 89.83 | 12.83 | 80.5% | 19.5% |
| balmoral | 13128 | 0 | 0 | 31.0% | 16.9% | 52.0% | 89.83 | 12.83 | 80.5% | 19.5% |

## Empirical lead time

- Not calculable from authoritative environmental observations yet.

## Clear-water secondary-cue test

- **palm-beach engineering fixture**: false-alert burden OFF 80.5%; ON 81.4%. Stable transitions/mo OFF 12.83; ON 12.89.
- **north-steyne engineering fixture**: false-alert burden OFF 80.5%; ON 81.4%. Stable transitions/mo OFF 12.83; ON 12.89.
- **bondi engineering fixture**: false-alert burden OFF 80.5%; ON 81.4%. Stable transitions/mo OFF 12.83; ON 12.89.
- **coogee engineering fixture**: false-alert burden OFF 80.5%; ON 81.4%. Stable transitions/mo OFF 12.83; ON 12.89.
- **cronulla engineering fixture**: false-alert burden OFF 80.5%; ON 81.4%. Stable transitions/mo OFF 12.83; ON 12.89.
- **balmoral engineering fixture**: false-alert burden OFF 80.5%; ON 81.4%. Stable transitions/mo OFF 12.83; ON 12.89.

## Validation gate

**EMPIRICAL VALIDATION REMAINS BLOCKED.** Synthetic fixture coverage proves ingestion/rules/hysteresis execution only; it does not establish shark-risk discrimination, lead time, or false-alert performance.

Missing observations are never interpreted as GREEN. `INSUFFICIENT_ENV_DATA` is a data-quality state, not a low-risk state.
