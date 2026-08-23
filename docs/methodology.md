# 4NICO Methodology Anchor

## A decision-support system, not an attack predictor

4NICO began with a tempting but ultimately misleading framing: could environmental and observation data be used to predict shark attacks? We rejected that framing because the event itself is too rare, too heterogeneous and too dependent on factors the system does not observe. A model can look impressive when asked to explain a handful of incidents after the fact while still being useless, or dangerous, as an operational tool.

The architecture therefore moved to a narrower and more defensible question: **what are the current shark-related environmental conditions, and how confident are we that the beach is being adequately observed?** These are different questions and the system keeps them separate.

The environmental state is GREEN, ORANGE or RED. It summarises configured environmental and verified-activity signals. The observation state is HIGH, MODERATE or BLACKOUT. It describes whether the system has enough surveillance support to interpret the environmental state with confidence. A beach can therefore have relatively quiet environmental conditions while observation is poor, or concerning environmental conditions while observation is strong. That distinction is operationally important. Lack of detections is not evidence of absence when surveillance itself is weak.

This dual-state design is the core architectural choice in 4NICO. It is intended to help a beach manager understand both **what the available environmental data says** and **how much confidence to place in the surrounding observation system**. It avoids collapsing uncertainty into a falsely precise single risk number.

## Why Alert Occupancy comes before incident prediction

The first validation question is not, “How many incidents did the model catch?” It is, “How often would this system tell a beach manager that conditions are elevated?”

We call that quantity **Alert Occupancy Rate**:

\[
\text{Alert Occupancy} = \frac{T_{Orange} + T_{Red}}{T_{Total}}
\]

This is the primary operational gate because an advisory system can fail even if it appears sensitive to historical incidents. If it remains ORANGE or RED most of the time, staff and the public will adapt to the warning. The signal becomes background noise. An operational system must therefore demonstrate that elevated states are sufficiently selective and stable to remain meaningful before incident hit-rate, discrimination or lead-time metrics become interesting.

Phase 0 made this point immediately. Across the synthetic engineering fixture, alert occupancy was 68.9 per cent. That is not evidence about real shark conditions, but it is a very useful engineering result: a system that behaved that way in the real world would impose an intolerable advisory burden. The baseline gives subsequent real-data substitutions something concrete to beat.

Incident prediction therefore comes second. Only after the system demonstrates a plausible advisory burden using observed multivariate data should we ask whether elevated states occur before verified incidents more often than an appropriate baseline would suggest. This ordering prevents rare-event performance from disguising an unusable day-to-day operating profile.

## Coogee as a falsification case

The 13 June 2026 Coogee shark incident is retained because it challenges the model rather than flattering it. Contemporary NSW Police and Randwick City Council reporting verifies a serious shark bite at Coogee that morning. The incident has also been associated with clear-water conditions, making it an important counterexample to any simplistic claim that rainfall, runoff or turbidity alone can identify all relevant conditions.

The methodological response is not to tune the thresholds until Coogee becomes RED. That would convert a difficult case into an exercise in retrospective curve fitting. Instead, Coogee is preserved as a falsification case: **if the core environmental architecture cannot represent the conditions around an important incident, that limitation must remain visible.**

This is why the rules engine is currently frozen. Secondary cues have been tested experimentally and did not justify inclusion at this stage. They remain outside the operational rules. Coogee stays in the validation set because a serious system should keep the observations most capable of proving it wrong.

## Provenance is part of the model

Incident data is not treated as a single undifferentiated list. 4NICO enforces three provenance classes:

- `ASID_AUTHORITATIVE`: the incident appears in the official Australian Shark-Incident Database release used by the pipeline.
- `VERIFIED_INTERIM`: the incident post-dates or is absent from that release but is supported by contemporaneous primary or named-authority sources, such as police or council reporting.
- `UNVERIFIED_SUPPLEMENTARY`: the report cannot support validation metrics because its evidentiary basis is insufficient.

Coogee is currently `VERIFIED_INTERIM`. It is verified strongly enough to retain as a validation event, but it must not be represented as if it were already part of the official ASID release.

Machine enforcement matters because provenance is otherwise easy to lose during joins, exports and repeated analysis. A spreadsheet row looks just as authoritative after its source column has been forgotten. By attaching provenance and validation eligibility to the incident record itself, the pipeline prevents supplementary reports from quietly leaking into hit-rate or lead-time calculations. It also preserves date precision: a month-only or year-only record is not promoted into an invented exact timestamp simply because the analytics code would prefer one.

## Missing data is an operational state

The system also refuses to interpret missing core environmental observations as reassuring conditions. If rainfall percentile, turbidity percentile or SST anomaly is unavailable, the environmental result becomes `INSUFFICIENT_ENV_DATA` and observation confidence becomes BLACKOUT. Missing values never silently become zero and never silently produce GREEN.

This is deliberately conservative. A municipal decision-support system should expose its inability to evaluate conditions rather than converting a data outage into apparent safety.

## Hysteresis and the problem of chatter

The first complete engineering fixture produced approximately 89.83 raw environmental state transitions per month. That is operationally absurd. A system changing state roughly three times a day would ask staff to track noise rather than useful changes in conditions.

The 24-hour de-escalation hold reduced that figure to 12.83 transitions per month. Escalation remains immediate, but a move to a lower environmental state must persist for 24 hours before the stable advisory de-escalates.

The result matters because it demonstrates that hysteresis is performing a real operational function independent of shark-risk validity. It suppresses rapid oscillation and creates a more legible state history. It does not prove that 24 hours is scientifically optimal, nor does it make the underlying thresholds causal. The hold is an operational configuration used to suppress chatter, and it remains frozen with the current rules engine while empirical displacement proceeds.

## What the system does not do

4NICO does **not** predict shark attacks, declare a beach safe, provide hour-ahead shark-risk forecasts, replace lifeguard or Surf Life Saving judgement, or substitute for official beach closures. It does not yet account for swimmer exposure, water-entry patterns or differences between activities such as surfing, swimming and wading. Its current purpose is narrower: communicate configured environmental conditions, verified recent activity and observation confidence, then measure whether that advisory behaviour is operationally tolerable. Those limits are not disclaimers attached after the fact; they define the system boundary.

## Validation by serial displacement

The validation strategy is deliberately incremental. Phase 0 used synthetic environmental fixtures to establish that ingestion, state evaluation, missing-data handling, hysteresis and reporting mechanics work end to end. Synthetic observations are quarantined from empirical performance claims.

The next phases replace one synthetic source at a time with observed data while keeping the rules engine fixed. Phase 1 substitutes observed BOM rainfall. Later phases displace hydrology, oceanography and beach-specific observations. Each substitution triggers a full 18-month rerun and records the change in Alert Occupancy and transition frequency. This makes the effect of each real dataset visible instead of replacing the entire evidence base at once and then arguing about which input caused what.

The governing principle is simple: **the validation machine is complete. The validated shark-risk model is not yet.**

**Phase 0 (synthetic baseline) complete. Phase 1 (observed rainfall) pending. No empirical hit-rate or lead-time claims justified yet.**
