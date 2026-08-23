# 4NICO Validation Roadmap

**Published:** 24 August 2026  
**Status:** Phase 0 complete. Phase 1 in execution.  
**Method status:** The validation machine is complete. The validated shark-risk model is not yet.

## Current Status

### Phase 0 — Synthetic Engineering Baseline

**COMPLETE**

- Alert Occupancy: **68.9%**
- Stable transitions after 24-hour de-escalation hold: **12.83/month**
- Raw transitions before hysteresis: **89.83/month**
- Result: the pipeline, state machine and hysteresis mechanism execute as designed.
- Interpretation: the synthetic advisory burden is operationally too high. This is an engineering baseline, not shark-risk evidence.

### Phase 1 — Observed Rainfall

**IN EXECUTION**

- Variable displaced: 72-hour rainfall signal
- Source: **BOM Station 066214, Sydney Observatory Hill**
- Remaining environmental layers: synthetic engineering fixtures
- Success condition: complete the 18-month rerun and record the exact change in Alert Occupancy and stable transitions/month relative to Phase 0.
- Public checkpoint: **after the first processed Phase 1 validation output lands on `main`**.

No calendar completion date is asserted until the Phase 1 runner completes successfully.

## Upcoming Phases

| Phase | Variable displaced | Intended source | Primary measurement | Status |
|---|---|---|---|---|
| 0 | None | Synthetic engineering fixtures | Baseline occupancy + transitions | Complete |
| 1 | Rainfall | BOM 066214 | Occupancy delta + transitions | In execution |
| 2 | Hydrology | WaterNSW turbidity/discharge | Occupancy delta + transitions | Queued |
| 3 | Oceanography | IMOS SST/upwelling | Occupancy delta + transitions | Queued |
| 4 | Remaining environmental observations | Observed sources | Full empirical advisory burden | Queued |
| 5 | Secondary cues | Full empirical series | ON/OFF ablation | Queued |

The rules engine remains frozen throughout this sequence. A source substitution is therefore measured against the same decision function rather than being accompanied by opportunistic retuning.

## Decision Gates

Alert Occupancy is the first operational gate:

`Alert Occupancy = (time ORANGE + time RED) / total classifiable time`

The following bands are **working governance gates for the validation program, not validated scientific thresholds**:

- **≤60%:** continue displacement while monitoring state stability.
- **60–65%:** continue cautiously and examine transition burden closely.
- **>65%:** pause before further interpretation; determine whether advisory burden remains operationally unusable before changing any rules.

A Phase 1 result above 65% does **not** automatically authorise threshold retuning. Any rules change creates a new documented validation phase and invalidates direct comparison with the frozen Phase 0 rules unless both versions are rerun.

Only after a substantially observed multivariate baseline exists should hit rate, lead time or discrimination be opened as empirical questions. A low occupancy number alone does not establish predictive value.

## What We Are Not Claiming Yet

4NICO does not currently claim:

- empirical shark-incident hit rate;
- empirical incident lead time;
- predictive power;
- beach safety classification;
- operational readiness for public deployment.

The current project establishes whether a transparent advisory system can remain usable as synthetic environmental inputs are replaced, one source at a time, by observations.

## Next Public Checkpoint

The next public checkpoint is the **Phase 1 validation result**: observed BOM rainfall substituted into the frozen 18-month pipeline, with the resulting Alert Occupancy and 24-hour-hold transition frequency compared directly with the locked Phase 0 baseline of **68.9%** and **12.83/month**.

**Phase 0 is locked. Phase 1 is pending completion. No empirical hit-rate or lead-time claims are justified yet.**
