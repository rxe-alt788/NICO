# 4NICO Technical Foundation Release

**Proposed tag:** `v0.1.0-methodology`  
**Release title:** `4NICO: Validation Methodology & Engineering Baseline (Phase 0 Complete)`  
**Release type:** Pre-release  
**Status:** Phase 0 synthetic engineering baseline complete. Phase 1 observed-rainfall validation in execution.

## What's Included

This release establishes the technical and methodological foundation for 4NICO, a shark-related beach-management decision-support prototype:

- **Methodology:** dual-state environmental + observation-confidence architecture, Alert Occupancy principle and falsification approach.
- **Engineering baseline:** 68.9% Alert Occupancy and 12.83 stable transitions/month under synthetic environmental fixtures.
- **Validation architecture:** serial displacement of synthetic inputs by observed sources while the rules engine remains frozen.
- **Incident provenance:** machine-enforced `ASID_AUTHORITATIVE`, `VERIFIED_INTERIM` and `UNVERIFIED_SUPPLEMENTARY` classes.
- **Operational boundaries:** explicit statement of what the system does, what it does not do and what remains unvalidated.

## Key Documents

- **Start here:** https://github.com/rxe-alt788/NICO/tree/main/docs
- **Methodology:** https://github.com/rxe-alt788/NICO/blob/main/docs/methodology.md
- **Validation roadmap:** https://github.com/rxe-alt788/NICO/blob/main/docs/validation_roadmap.md
- **Scope and limitations:** https://github.com/rxe-alt788/NICO/blob/main/docs/scope_and_limitations.md
- **Rules engine:** https://github.com/rxe-alt788/NICO/blob/main/docs/rules_engine_specification.md
- **Incident provenance:** https://github.com/rxe-alt788/NICO/blob/main/docs/incident_provenance_schema.md
- **Visuals:** https://github.com/rxe-alt788/NICO/tree/main/docs/visuals

## Current Validation Status

| Phase | Variable | Source | Status |
|---|---|---|---|
| 0 | None | Synthetic engineering fixtures | **COMPLETE** |
| 1 | Rainfall | BOM Station 066214 | **IN EXECUTION** |
| 2 | Hydrology | WaterNSW | Queued |
| 3 | Oceanography | IMOS | Queued |
| 4 | Full observed environmental series | Multiple observed sources | Queued |
| 5 | Secondary-cue ablation | Full empirical series | Queued |

## Engineering Result

The Phase 0 synthetic fixture produced **68.9% Alert Occupancy**, which is operationally excessive and therefore a useful baseline failure rather than a performance claim.

The 24-hour environmental de-escalation hold reduced state changes from **89.83 raw transitions/month to 12.83 stable transitions/month**, demonstrating that the hysteresis mechanism substantially suppresses advisory chatter.

These results validate pipeline and state-machine mechanics only.

## Important Boundary

**This is not a validated shark-risk model.**

4NICO does not predict shark attacks, declare beaches safe, or currently justify empirical hit-rate, lead-time or discrimination claims.

**The validation machine is complete. The validated shark-risk model is not yet.**

Phase 0 is locked. Phase 1 will provide the first observed-data displacement result by replacing synthetic rainfall with BOM Station 066214 while the remaining environmental layers and the rules engine remain unchanged.

## Next Checkpoint

The next public checkpoint will be published when the Phase 1 processed validation output completes successfully and the observed-rainfall delta in Alert Occupancy and stable transitions/month can be reported.

Questions and technical feedback can be raised through the repository's GitHub Issues or Discussions features.
