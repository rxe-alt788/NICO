# 4NICO

4NICO communicates **environmental conditions + observation confidence** to support beach-management decisions. It does **not** predict shark attacks or declare beaches safe. The system separates an environmental state (`GREEN`, `ORANGE`, `RED`) from observation confidence (`HIGH`, `MODERATE`, `BLACKOUT`) so missing or degraded surveillance cannot masquerade as reassurance.

For the design rationale, falsification method and validation approach, read [docs/methodology.md](docs/methodology.md). Operational boundaries are in [docs/scope_and_limitations.md](docs/scope_and_limitations.md), incident provenance in [docs/incident_provenance_schema.md](docs/incident_provenance_schema.md), and the frozen rules in [docs/rules_engine_specification.md](docs/rules_engine_specification.md).

## Validation status

**The validation machine is complete. The validated shark-risk model is not yet.**

- **Phase 0 baseline:** complete synthetic engineering fixture; **68.9% Alert Occupancy** and **12.83 transitions/month** after the 24-hour de-escalation hold.
- **Phase 1:** observed BOM rainfall from Sydney Observatory Hill station **066214** is in validation.
- WaterNSW hydrology, IMOS oceanography and Beachwatch inputs remain synthetic in the completed baseline.
- The rules engine is frozen. Thresholds are configurable operating rules, not validated science.
- **Empirical hit-rate, lead-time and discrimination claims remain pending Phase 1 and later real-data displacement.**

## Run validation

Locally, with Python 3.12:

```bash
python -m pip install -r requirements-validation.txt
python scripts/bootstrap_raw_data.py
python scripts/fetch_bom_cdo.py
python scripts/ingest_historical.py
python scripts/run_validation.py
```

The canonical pipeline is `.github/workflows/model_validation.yml`, which can also be started with **Run workflow** from GitHub Actions. Raw inputs are kept as workflow artifacts; only processed validation outputs are committed.

## Current sources

| Source | Current validation status |
|---|---|
| BOM rainfall | Observed Phase 1 source, station 066214 |
| WaterNSW | Synthetic pending displacement |
| IMOS | Synthetic pending displacement |
| Beachwatch | Synthetic pending displacement |
| ASID/DPI | ASID authoritative release + controlled verified-interim ledger |

Questions and review comments should be raised through this repository's GitHub Issues so technical and methodological decisions remain visible with the work.
