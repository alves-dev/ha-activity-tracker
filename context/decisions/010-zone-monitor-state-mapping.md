# Decision: Zone Monitor State Mapping

## Context

Zone monitors store the selected zone as a `zone.*` entity ID, while Home
Assistant reports a tracked person's or device tracker's location as `home` or
the name of a zone. Comparing the two values directly made a configured zone
monitor inactive during normal operation.

## Decision

Keep the selected zone entity ID as configuration identity. At classification
time, derive the comparable source state as follows:

- `zone.home` maps to `home`.
- Any other loaded zone maps to its current name.
- Before a non-home zone entity is available, use its entity-ID object part as a
  safe startup fallback.

## Rationale

This follows Home Assistant's person and device-tracker state contract without
requiring configuration migration or changing the zone selected by the user.
The explicit home rule avoids a localized or customized zone display name from
breaking standard home presence.

## Alternatives Considered

- Compare directly with `zone.*`. Rejected because it is not the state emitted by
  person and device-tracker entities.
- Persist a duplicated zone state string. Rejected because renaming a zone would
  make the monitor stale.

## Outcomes

Implemented on 2026-08-27. Zone classification now resolves the selected zone
at runtime and is covered for home, fallback, and named-zone cases.

## Related

- [Feature: Flexible Activity Monitoring](../intent/feature-flexible-activity-monitoring.md)
- [Pattern: Activity State Classification](../knowledge/patterns/activity-state-classification.md)
- [Decision: Home Assistant Config-Entry Integration](002-home-assistant-integration-architecture.md)

## Status

- **Created**: 2026-08-27
- **Status**: Accepted
