# Frozen Rules Engine Specification

**Frozen as of 24 August 2026.** The current rules are deterministic configuration, not validated causal science. Any change to thresholds, weights, missing-data behaviour or hysteresis should be treated as a new validation phase rather than silently replacing the baseline.

## 1. Environmental inputs

The engine requires three core environmental fields:

- `rainPct`: percentile rank of 72-hour rainfall accumulation.
- `turbidityPct`: turbidity percentile rank.
- `sstAnomaly`: sea-surface-temperature anomaly in degrees Celsius.

It may also receive `recentTagDetected`, representing a verified recent tagged-shark detection. The current configuration defines “recent” as 24 hours.

If any core environmental field is missing or non-finite, the engine does not calculate a GREEN/ORANGE/RED score. It returns:

- environmental state: `INSUFFICIENT_ENV_DATA`
- observation state: `BLACKOUT`
- composite: `INSUFFICIENT_ENV_DATA_BLACK`
- environmental score: `null`
- confidence score: `0`

Missing values are never converted to zero.

## 2. Environmental score

Current configuration:

| Signal | Condition | Score |
|---|---:|---:|
| 72h rainfall | >= 90th percentile | +2 |
| 72h rainfall | >= 75th and <90th percentile | +1 |
| Turbidity | >= 80th percentile | +2 |
| Turbidity | >= 50th and <80th percentile | +1 |
| SST anomaly | >= +1.5 C | +1 |
| Verified recent tag detection | true | +3 |

Only the highest applicable rainfall contribution and highest applicable turbidity contribution are used.

Environmental state:

- score 0-1: `GREEN`
- score 2: `ORANGE`
- score >=3: `RED`
- a verified recent tag detection also forces `RED`

These thresholds and weights are **configurable operating rules, not validated scientific thresholds**. Their purpose during the current program is to provide a frozen decision function against which successive real-data substitutions can be compared.

Experimental secondary cues have been tested and are disabled by default. They are not part of the frozen operational specification.

## 3. Observation confidence

Observation confidence is a separate three-point score. One point is awarded for each available condition:

1. `droneActive`
2. `lifeguardActive`
3. `turbidityDataOk`

The observation state is:

- score 3: `HIGH`
- score 2: `MODERATE`
- score 0-1: `BLACKOUT`

This means a low environmental score never implies good observation. Environmental state and confidence remain separate.

The current composite output appends `_BLACK` when observation confidence is BLACKOUT, for example `RED_BLACK`. HIGH and MODERATE retain the environmental flag in the current code while the observation state remains separately available to the interface and analytics.

## 4. Hysteresis

Escalation is immediate. If the candidate environmental state is equal to or more severe than the stable state, the stable state changes immediately.

De-escalation requires the lower candidate state to persist for **24 hours**. If the candidate rises again during that window, the lower-state hold is reset.

The purpose of the 24-hour hold is operational: suppress rapid state chatter. In the Phase 0 engineering fixture it reduced raw transitions from **89.83 per month to 12.83 per month**. This demonstrates damping behaviour, not scientific optimality of a 24-hour interval.

`INSUFFICIENT_ENV_DATA` is not forced through the GREEN/ORANGE/RED hysteresis path. A data-quality failure is exposed directly.

## 5. Worked example

Inputs:

- rainfall percentile: 85th (`0.85`)
- turbidity percentile: 60th (`0.60`)
- SST anomaly: `+0.3 C`
- one verified tag detection occurred sometime in the last 48 hours
- drone active: yes
- lifeguard active: yes
- turbidity data available/current: yes

The phrase “in the last 48 hours” is not precise enough for the frozen engine because its configured tag window is **24 hours**.

Environmental score without a qualifying recent tag:

- rainfall >=75th percentile: +1
- turbidity >=50th percentile: +1
- SST anomaly below +1.5 C: +0

Subtotal: **2**, producing `ORANGE`.

If the verified tag detection occurred **within the last 24 hours**, `recentTagDetected=true`. The engine adds +3 and independently forces `RED`, giving a final score of **5**. With all three observation inputs available, confidence score is 3 and the state is **RED + HIGH**.

If the detection occurred **more than 24 hours ago but no more than 48 hours ago**, it is outside the current configured tag window. No tag points are added. The environmental state remains **ORANGE** and the observation state is **HIGH**.

This distinction is deliberate documentation of the frozen engine, not threshold tuning.

**The validation machine is complete. The validated shark-risk model is not yet.**
