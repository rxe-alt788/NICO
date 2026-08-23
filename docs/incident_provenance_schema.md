# Incident Provenance Schema

4NICO treats incident provenance as part of the validation logic, not as optional metadata. Every incident record must carry one of three allowed provenance classes.

## Taxonomy

### `ASID_AUTHORITATIVE`
Use when the incident is published in the official Australian Shark-Incident Database release used by the pipeline. The record inherits ASID as its authoritative source, while any 4NICO pilot-beach mapping remains separately labelled as an analytical mapping.

### `VERIFIED_INTERIM`
Use when an incident is not yet present in the current ASID release but is supported by contemporaneous primary or named-authority sources. Suitable evidence includes NSW Police, a local council, Surf Life Saving or equivalent emergency reporting, or reputable reporting that directly attributes the event to a named authority.

### `UNVERIFIED_SUPPLEMENTARY`
Use when the evidentiary basis is insufficient for validation, for example a crowdsourced sighting, Reddit post, rumour, unattributed social-media report or other unconfirmed account. These records may be retained for research but are excluded from validation metrics.

## Coogee example: 13 June 2026

The Coogee incident is classified `VERIFIED_INTERIM`.

Source chain:
1. NSW Police reported that emergency services were called to Coogee Beach just before 11:15 am on 13 June 2026 after a swimmer was bitten by a shark and suffered serious arm and leg injuries.
2. Randwick City Council independently reported a serious shark incident at Coogee Beach that morning and closed council-managed eastern-suburbs beaches as a precaution.
3. The event post-dates the official ASID release currently used by the pipeline, so it must not be labelled `ASID_AUTHORITATIVE` until formally reconciled.

## Required preserved fields

Where present in the source, incident records preserve: incident identifier, location, state, latitude, longitude, species/common and scientific name, species-identification method/source, shark length, injury outcome, fatality status, victim activity, provoked/unprovoked status, site category, presence at time of bite, incident year/month, timestamp and date precision.

Date precision is explicit. A month-only or year-only ASID record remains month-only or year-only. **4NICO does not invent an exact timestamp to make analytics easier.**

## Why enforcement is machine-level

Validation eligibility is attached to the record itself. Analytics accept only `ASID_AUTHORITATIVE` and `VERIFIED_INTERIM` records explicitly marked eligible. This prevents supplementary observations from leaking into hit-rate or lead-time metrics during merges, exports or later analysis.

**The validation machine is complete. The validated shark-risk model is not yet.**
