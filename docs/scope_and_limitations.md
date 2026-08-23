# 4NICO Scope and Limitations

## 1. What This System Does

4NICO is a municipal decision-support prototype for beach operations. It communicates:

- current configured environmental conditions as `GREEN`, `ORANGE` or `RED`;
- observation confidence as `HIGH`, `MODERATE` or `BLACKOUT`;
- recent verified shark activity where available;
- Alert Occupancy, the proportion of classifiable time spent ORANGE or RED, as a measure of operational advisory burden.

Environmental state and observation confidence are deliberately separate. Poor observation is not interpreted as reassuring conditions.

## 2. What This System Does NOT Do

4NICO does not:

- predict shark attacks;
- declare beaches safe;
- provide hour-ahead shark-risk forecasts;
- currently account for human behaviour, water-entry patterns or activity type such as surfing, swimming or wading;
- replace lifeguard judgement, Surf Life Saving procedures, NSW Government shark-management measures or official beach closures.

Its current role is to test whether a transparent environmental and confidence advisory can behave usefully enough to justify further validation.

## 3. Audience

The intended users are beach managers, council operations teams and Surf Life Saving or surf-club officials reviewing operational conditions and system confidence.

The current prototype is **not an individual-swimmer risk tool**. Individual swimmers need decision support that accounts for personal exposure, activity and immediate local conditions beyond the present model boundary.

## 4. Current Validation Status

**Phase 0 is complete.** The synthetic engineering baseline produced **68.9% Alert Occupancy** and **12.83 environmental transitions per month after the 24-hour de-escalation hold**.

**Phase 1 is in execution.** Synthetic rainfall is being displaced by observed daily rainfall from BOM Sydney Observatory Hill station 066214 while the rest of the environmental series remains synthetic.

Phases 2-5 are queued and progressively replace hydrology, oceanography, beach telemetry and later validation components with observed sources.

**No empirical hit-rate, lead-time or discrimination claims are justified yet.** Phase 0 establishes pipeline behaviour, not shark-risk performance.

## 5. Known Limitations

- Rainfall currently uses Sydney Observatory Hill station 066214 as a single-gauge proxy across six pilot beaches. It is not yet catchment-specific.
- WaterNSW hydrology and IMOS/Beachwatch environmental inputs remain synthetic in the current completed baseline.
- The authoritative incident series is limited by the official ASID release used by the pipeline. Later incidents can enter only through the separately controlled `VERIFIED_INTERIM` provenance class until ASID reconciliation.
- The rules are deterministic configuration, not learned from data and not validated causal thresholds.
- Missing core environmental data produces `INSUFFICIENT_ENV_DATA + BLACKOUT`; it is never silently treated as GREEN.

## 6. What Changes Next

The immediate next result is the Phase 1 Alert Occupancy and transition-rate delta after replacing synthetic rainfall with observed BOM data. Later phases will add observed hydrology, oceanography and more beach-specific telemetry while keeping the rules engine fixed so each displacement can be measured cleanly.

Incident lead-time analysis is future work and should be treated seriously only after multivariate real-data baselines exist.

**The validation machine is complete. The validated shark-risk model is not yet.**
