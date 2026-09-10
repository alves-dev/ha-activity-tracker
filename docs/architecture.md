# Storage and sensor contract

Every monitor owns `.storage/activity_tracker.<config-entry-id>`. Its payload is
schema v3 and stores compact local-day aggregates, one active-session checkpoint,
and the latest completed session. Detailed completed sessions are never retained.
Schema v3 is intentionally incompatible with earlier payloads: the integration
does not migrate previous storage, config entries, entity identifiers, statistics,
or Recorder history.

Rules are persisted as independent `start_when` and `stop_when` expressions.
Each expression is an `all` or `any` tree of state, numeric-state,
report-silence, or template leaves. Numeric-state leaves compare exact decimal
values from an entity state or optional attribute. The runtime subscribes to referenced entities and schedules the earliest
eligible deadline; it never polls to make accounting decisions. For a template
leaf, Home Assistant's template tracker discovers the referenced entities and
attributes dynamically and re-evaluates the rule when its boolean result changes.

Completed sessions are attributed according to the monitor's cross-midnight
policy. `started_day` and `ended_day` assign the full duration and one session to
one date. `split_at_midnight` assigns each real local-time fragment and one
session to each participating date. Start and end circular time components are
stored separately for period averages.

Durations are retained in exact seconds. Duration sensors publish the monitor's
selected seconds, minutes, or hours unit. Only the current-day total-duration
sensor has the `total_increasing` state class, producing `sum` statistics for
the Home Assistant daily graph; all other totals are measurements.

The admin-only **Activity Rules** sidebar receives a recursive live rule
snapshot through a websocket subscription. It is a locally served custom
element that uses Home Assistant theme variables. Its complete editor keeps
only an unsaved draft in the browser; protected integration commands validate
the contract, preview templates, calculate the review diff, classify history
impact, and apply the entry. The panel never hosts config flows or writes a
config entry directly. Updating rules does not clear summaries; an active
session is restored across the entry reload and remains open until a later
evaluation matches the new stop rule.
