# 4NICO Documentation

**Published:** 24 August 2026  
**Status:** Phase 0 complete. Phase 1 in execution.

4NICO is a beach-management decision-support prototype. It communicates configured environmental conditions and observation confidence. It does **not** predict shark attacks or declare beaches safe.

> **The validation machine is complete. The validated shark-risk model is not yet.**

## Start Here

- [Methodology](methodology.md) — why the system uses environmental state + observation confidence, why Alert Occupancy is the primary operational gate, and how falsification is treated.
- [Validation Roadmap](validation_roadmap.md) — Phase 0 baseline, Phase 1 execution, serial displacement sequence and decision gates.
- [Scope and Limitations](scope_and_limitations.md) — what 4NICO does, what it does not do, intended audience and current validation boundaries.
- [Frozen Rules Engine Specification](rules_engine_specification.md) — exact configured thresholds, missing-data behaviour, observation-confidence logic and hysteresis.
- [Incident Provenance Schema](incident_provenance_schema.md) — machine-enforced incident lineage and the Coogee `VERIFIED_INTERIM` example.

## Visuals

- [State Machine Grid](visuals/state_machine_grid.svg) — nine environmental × observation-confidence states and the 24-hour de-escalation hold.
- [Data Pipeline Architecture](visuals/data_pipeline_architecture.svg) — source → ingestion/provenance → frozen rules → outputs and CI/CD audit loop.
- [Serial Displacement Sequence](visuals/serial_displacement_sequence.svg) — how real sources replace synthetic fixtures without changing the rules engine.

## Current Validation Position

| Phase | Data state | Alert Occupancy | Stable transitions/month | Status |
|---|---|---:|---:|---|
| 0 | Synthetic environmental fixture | **68.9%** | **12.83** | Complete |
| 1 | Observed BOM rainfall + synthetic remainder | Pending | Pending | In execution |
| 2–5 | Progressive observed hydrology/oceanography/full series | Pending | Pending | Queued |

The Phase 0 numbers demonstrate engineering behaviour only. They do not establish shark-risk discrimination, incident hit rate or lead time.

## Audience Guide

**Beach managers / council operations:** start with [Scope and Limitations](scope_and_limitations.md) and the [State Machine Grid](visuals/state_machine_grid.svg).

**Funders / partners:** start with the [Validation Roadmap](validation_roadmap.md), [Methodology](methodology.md) and [Serial Displacement Sequence](visuals/serial_displacement_sequence.svg).

**Researchers:** start with [Methodology](methodology.md), [Incident Provenance](incident_provenance_schema.md) and the current validation report under `data/`.

**Engineers:** start with the [Rules Engine Specification](rules_engine_specification.md), [Pipeline Architecture](visuals/data_pipeline_architecture.svg) and `.github/workflows/model_validation.yml`.

## Current Hard Boundary

**Phase 0 (synthetic baseline) is complete. Phase 1 (observed rainfall) is pending completion. No empirical hit-rate, lead-time or discrimination claims are justified yet.**
