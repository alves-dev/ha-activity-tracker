# Activity Tracker — Implementation Specification

## 1. Document purpose

This document specifies the first version of **Activity Tracker**, a custom Home Assistant integration that measures how long an entity remains active and how many activity sessions occur within configured periods.

The integration abstracts and extends the idea behind Home Assistant's `history_stats` integration. Instead of depending permanently on Recorder history, Activity Tracker observes state changes in real time and stores compact daily summaries after activity is observed.

The specification is intended to provide enough functional and technical direction for an implementation agent to build the MVP without redefining product behavior.

## 2. Product identity

- **Name:** Activity Tracker
- **Domain:** `activity_tracker`
- **UI languages:** English and Brazilian Portuguese (`pt-BR`)
- **Integration type:** custom Home Assistant integration
- **Configuration:** UI only through Config Flow and Options Flow
- **YAML configuration:** not required for the MVP

## 3. Main goals

Activity Tracker must allow a user to answer questions such as:

- How long was the living room TV on today, this week, or this month?
- How many times did I visit the barber during the last 35 days?
- How long was my latest visit to the barber?
- How much time did a person spend in a selected zone?
- How much time did a person spend in an internal Home Assistant area?
- Which weekday accumulated the most activity?
- Which application remained in the foreground the longest on a device?
- How many activity sessions happened within a custom rolling period?

The integration must prioritize:

- Simple configuration through Home Assistant's UI.
- Reliable session tracking across restarts and day boundaries.
- Compact long-term storage independent of Recorder retention.
- User-selected sensors instead of creating every possible entity.
- Clear distinction between observed, estimated, and unknown time.

## 4. Non-goals for the MVP

The following are explicitly outside the first version:

- A custom dashboard or frontend panel.
- Permanent storage of every historical session.
- Manual editing of completed sessions.
- Aggregation across different monitor entries.
- Rankings between different devices, people, zones, or areas.
- Numeric threshold rules.
- Rules based on entity attributes, except for foreground application value extraction.
- Boolean expressions combining multiple entities.
- Automatic inference of activities from duration, such as deciding whether a barber visit was beard-only or haircut-and-beard.
- Background application tracking.
- Automatic classification of launchers, lock screens, or system applications.

## 5. Core terminology

### 5.1 Monitor

A **monitor** is one Home Assistant config entry. Each monitor has its own source, rule, retention, interruption behavior, selected periods, and selected sensors.

Examples:

- `Living room TV on`
- `Igor at the gym`
- `Igor in the office`
- `Igor phone applications`
- `Xbox active`
- `Barber`

Each config entry must create one virtual Home Assistant device containing the entities selected for that monitor.

### 5.2 Activity

Activity is the logical condition produced by the monitor rule. For a generic state monitor:

```text
active = source_entity.state is in configured_active_states
```

### 5.3 Session

A session is one continuous logical activity interval. Changing between two active states does not create a new session.

Example:

```text
playing -> paused -> playing
```

This remains one session when all three states are configured as active.

For a foreground application monitor, changing the application always ends the current application session and starts another one.

### 5.4 Daily summary

A daily summary is the permanent aggregate stored for a monitor and local calendar date. Detailed historical sessions are not retained after consolidation.

### 5.5 Checkpoint

A checkpoint is the small persisted runtime structure required to resume or safely close the current activity after a Home Assistant restart. It is not a historical session archive.

### 5.6 Period

A period defines the date range used by a sensor. The MVP supports calendar periods and rolling calendar-day periods.

## 6. Monitor types

The setup flow must begin by asking the user to select a monitor type.

### 6.1 Entity active states

Tracks any entity while its state belongs to a configured list.

Example:

```yaml
type: entity_state
entity_id: media_player.living_room_tv
active_states:
  - "on"
  - "playing"
  - "paused"
  - "idle"
```

State changes within the active list do not split the session.

### 6.2 Person or device in zone

Tracks one `person` or `device_tracker` entity while it is inside exactly one selected Home Assistant zone.

Example:

```yaml
type: zone
entity_id: person.igor
zone_entity_id: zone.barber
```

Only the selected zone counts as active. `home`, `not_home`, and other zones must not count unless they are the selected zone in another monitor.

The implementation must store the zone entity ID rather than relying only on its display name. Zone renames must not silently break the monitor.

### 6.3 Person in internal area

Tracks a person in an internal Home Assistant area using a dedicated binary sensor.

Home Assistant areas do not inherently identify which person is present. Therefore, the activity source must be an explicit `binary_sensor` chosen by the user.

Example:

```yaml
type: area_presence
person_entity_id: person.igor
area_id: office
presence_entity_id: binary_sensor.igor_in_office
active_states:
  - "on"
```

The selected person and area provide identity and naming. The binary sensor is the authoritative activity source.

The UI should suggest binary sensors assigned to the selected area first, while still allowing any binary sensor to be selected.

### 6.4 Foreground application

Tracks the foreground application reported by one entity. The application value may come from:

- The entity state.
- One user-selected entity attribute.

Example using the state:

```yaml
type: foreground_application
entity_id: sensor.igor_phone_foreground_app
value_source: state
```

Example using an attribute:

```yaml
type: foreground_application
entity_id: sensor.living_room_tv
value_source: attribute
value_attribute: app_id
label_attribute: app_name
```

If both an identifier and label are available, the stable identifier must be used for storage and the label for display. If only one value is available, it acts as both identifier and label.

Only the foreground application is tracked in the MVP. Background media or simultaneous applications are not tracked.

Launchers, lock screens, System UI, and similar applications are treated like any other application. The integration must not ignore them automatically. Users may explicitly ignore applications later through Options Flow.

### 6.5 Generic monitor

Provides the same active-state engine without specialized zone, area, device, or application language.

The MVP generic rule supports only a list of active states:

```yaml
type: generic
entity_id: input_select.custom_activity
active_states:
  - active
  - running
```

## 7. Configuration model

Each monitor is a separate config entry. A config entry must contain stable identity and rule-defining values. User-adjustable behavior belongs in entry options where appropriate.

Conceptual model:

```yaml
entry:
  name: Living room TV on
  monitor_type: entity_state
  entity_id: media_player.living_room_tv
  active_states:
    - "on"
    - "playing"
    - "paused"
    - "idle"

options:
  retention_days: 90
  minimum_session_seconds: 0
  unavailable_behavior: unknown
  unavailable_tolerance_seconds: 0
  merge_gap_seconds: 0
  import_recorder_history: false
  periods:
    - current_day
    - current_week
    - current_month
    - rolling_days: 35
  enabled_metrics:
    - total_duration
    - session_count
    - current_session_duration
    - last_session_duration
```

### 7.1 Required setup choices

The user must explicitly select all sensors and periods during creation. No metric sensor set is enabled implicitly.

The flow must prevent completing setup without selecting at least one sensor.

### 7.2 Default values

- Retention: `90` days.
- Minimum session duration: `0` seconds, meaning no minimum.
- Language: English.
- Update resolution during active activity: once per minute.
- Week boundaries: Home Assistant global/local configuration.
- Time zone: Home Assistant configured time zone.

### 7.3 Retention validation

- Retention is configured as a user-defined number of days.
- The UI should enforce a reasonable minimum, recommended as 7 days.
- A selected rolling or analytical period must not exceed retention.
- If an existing configuration becomes inconsistent, affected sensors must become unavailable with a clear reason.
- Reducing retention schedules deletion of older summaries during the next cleanup.
- Increasing retention cannot recreate previously deleted data unless it is reimported from Recorder.

## 8. Supported periods

### 8.1 Calendar periods

- Current day.
- Current week.
- Current month.

Current calendar-period sensors are available immediately and accumulate from the available observation start. They do not require the calendar period to be complete.

The current week must respect the Home Assistant global week convention. The implementation must not hardcode Monday or Sunday if a supported HA locale/configuration API provides the boundary.

### 8.2 Custom rolling calendar days

The user may configure any positive whole number of rolling calendar days, such as 7, 30, 35, 60, or 180 days.

Example:

```yaml
type: rolling_days
days: 35
```

Rolling days mean today plus the previous `N - 1` local calendar dates. They do not mean an exact `N * 24` hour duration from the current instant.

For a 35-day sensor on August 26, the range begins at local midnight 34 dates earlier and ends at the current moment for live duration values.

### 8.3 Completeness

Current day, week, and month sensors are available immediately.

Sensors that promise a complete rolling window or historical analysis must be `unavailable` until enough complete days exist.

Example attributes:

```yaml
reason: insufficient_history
required_days: 35
available_days: 18
available_from: "2026-08-08"
```

The first day begins at the exact monitor creation time when no history is imported. It must be stored as a partial day and excluded from analytics requiring full days.

## 9. Session lifecycle

### 9.1 Session start

A session begins when the source transitions from inactive to active.

The integration must persist enough checkpoint state promptly so a Home Assistant restart does not lose the observed start.

### 9.2 Session continuation

- Transitions between configured active states keep the same session.
- Foreground application changes end one application session and begin another.
- Repeated state events without a logical change must not duplicate sessions.

### 9.3 Session end

A session ends when the source becomes inactive, subject to configured unavailable and merge-gap behavior.

### 9.4 Crossing midnight

A session crossing local midnight must have its duration split exactly across daily summaries.

Example:

```text
Monday 23:30 -> Tuesday 01:30
```

Results:

- Monday duration: 30 minutes.
- Tuesday duration: 90 minutes.
- `sessions_started` increments only on Monday.
- Tuesday records a continuation but not a newly started session.

Suggested daily fields:

```yaml
sessions_started: 0
continued_sessions: 1
```

Session count sensors must sum `sessions_started`, not `continued_sessions`.

### 9.5 Minimum session duration

Minimum duration is configurable per monitor and has no non-zero default.

The minimum applies to the complete continuous session, even when it crosses day boundaries.

Example with a five-minute minimum:

```text
23:58 -> 00:04 = six-minute valid session
```

Both daily portions are valid even though each portion is shorter than five minutes.

Before the session reaches the minimum, its portions must remain pending in the checkpoint. Once it reaches the threshold, the pending portions may be committed. If it ends before the threshold, it is discarded.

### 9.6 Current session

The current-session sensor must update once per minute while active. The integration must calculate the displayed value in memory without writing storage every minute.

### 9.7 Last completed session

Daily summaries cannot reconstruct the exact latest session. Therefore, each monitor must persist metadata for the latest completed valid session:

```yaml
last_completed_session:
  started_at: "2026-08-20T14:10:00-03:00"
  ended_at: "2026-08-20T15:25:00-03:00"
  duration_seconds: 4500
  quality: exact
  crossed_midnight: false
```

This record is not considered permanent detailed session history.

Required possible sensors:

- Last session duration.
- Last session start.
- Last session end.
- Days since last session.

## 10. Interruption, unavailable, and restart behavior

### 10.1 Per-monitor configuration

Unavailable behavior is configured independently for each monitor. Different sources have different reliability characteristics.

The implementation should support options equivalent to:

- End activity when unavailable.
- Keep activity pending for a configured tolerance.
- Treat the interval as unknown.
- Resume as one logical session when the source returns active within tolerance.

### 10.2 Home Assistant downtime

When Home Assistant stops observing and later restarts, the unobserved interval must be classified as unknown by default. The integration must not claim the source stayed active without evidence.

Example:

```text
Last observed active: 22:30
Home Assistant available again: 22:40
Current source state: active
```

Expected result:

- Activity through 22:30 is exact.
- 22:30 through 22:40 is unknown.
- Activity resumes from 22:40.
- The logical visit/use may remain one session if tolerance permits, but unknown seconds are not added to active duration.

### 10.3 Merge gap

Zone and presence sources can briefly leave and return because of GPS or radio noise. Each monitor must offer a configurable merge gap.

Example:

```text
Barber -> not_home for 20 seconds -> Barber
```

If the inactive gap is within the configured threshold:

- Keep one logical session.
- Exclude the inactive gap from active duration.
- Do not increment session count again.

This differs from unavailable tolerance: merge gap applies to a real observed inactive state, while unavailable tolerance applies to missing/unknown source data.

## 11. Storage model

### 11.1 Storage principle

The integration must permanently store only:

- Configuration and rule metadata.
- Runtime checkpoint.
- One consolidated summary per local calendar day.
- Latest completed valid session metadata.
- Foreground application discovery metadata and per-day application aggregates.

It must not retain a permanent list of every completed session.

### 11.2 Suggested Home Assistant storage

Use versioned Home Assistant storage, conceptually separated per config entry:

```text
.storage/activity_tracker.<config_entry_id>
```

The implementation may use one integration-level store if it provides safe per-entry isolation and efficient updates. Storage format must be versioned and migratable.

### 11.3 Daily summary schema

Conceptual schema:

```yaml
date: "2026-08-26"
rule_version: 1

total_seconds: 14400
sessions_started: 3
continued_sessions: 0
longest_session_seconds: 7200
shortest_session_seconds: 1800

first_active_at: "08:20:00"
last_inactive_at: "22:45:00"

exact_seconds: 13800
estimated_seconds: 0
unknown_seconds: 600

coverage_start: "00:00:00"
coverage_end: "23:59:59"
complete: true
```

Do not store values that are cheaply derived. For example, average session duration is:

```text
total valid session duration / sessions started in the selected period
```

Handle continuation-only periods carefully so division remains meaningful.

### 11.4 Checkpoint schema

Conceptual schema:

```yaml
active: true
started_at: "2026-08-26T20:10:00-03:00"
last_observed_at: "2026-08-26T22:30:00-03:00"
source_state: playing
minimum_reached: true
pending_daily_parts: {}
excluded_gap_seconds: 0
unknown_gap_seconds: 0
```

### 11.5 Write strategy

Do not write storage on every minute tick. Persist on meaningful events:

- Session start.
- Session end.
- Foreground application change.
- Local midnight.
- Home Assistant shutdown.
- Import completion or checkpoint.
- History cleanup.
- Configuration change.

Minute updates for active sensors should remain in memory.

### 11.6 Retention cleanup

- Run cleanup once per day after the local day boundary.
- Delete summaries older than the configured retention.
- Clean foreground application aggregates consistently.
- Keep storage writes atomic.
- If cleanup makes an analysis period incomplete, its sensor becomes unavailable.
- Removing a config entry deletes its summaries, checkpoint, and related metadata automatically.

Before entry removal, the UI must clearly warn that historical summaries will be permanently deleted.

## 12. Foreground application aggregation

### 12.1 Discovery

The monitor discovers application identifiers as they appear.

Conceptual metadata:

```yaml
applications:
  com.google.android.youtube:
    display_name: YouTube
    first_seen: "2026-08-26"
    last_seen: "2026-08-26"
    ignored: false
    individual_sensors_enabled: true
```

Applications remain separated by device because every foreground application monitor is a separate config entry. Do not combine YouTube usage across phone, tablet, and TV.

### 12.2 Daily application summary

```yaml
date: "2026-08-26"
total_seconds: 18000
applications:
  com.google.android.youtube:
    display_name: YouTube
    total_seconds: 5400
    sessions_started: 3
    longest_session_seconds: 2700
  com.android.chrome:
    display_name: Chrome
    total_seconds: 3600
    sessions_started: 5
    longest_session_seconds: 1500
```

### 12.3 Application entity control

Discovering an application must not automatically create entities for it.

Options Flow must allow the user to classify discovered applications as:

- Included in general summaries with individual sensors.
- Included in general summaries without individual sensors.
- Ignored from future activity totals.

The MVP does not need retroactive reclassification beyond the general rule-change handling described later.

Entity IDs must remain stable if an application display label changes.

## 13. Sensor catalog

The creation flow must let the user select periods and metrics. Only selected combinations create entities.

All duration sensors should expose numeric native values compatible with Home Assistant duration semantics. Internally, all duration arithmetic uses seconds. A human-readable formatted value may be exposed as an attribute but not as the numeric state.

### 13.1 Current activity sensors

- Active binary sensor.
- Current session duration.
- Current foreground application, when applicable.

### 13.2 Duration sensors

For every selected period:

- Total activity duration.
- Average daily duration.
- Average session duration.
- Longest session duration.
- Shortest session duration, if supported.

Examples:

```text
sensor.living_room_tv_duration_today
sensor.living_room_tv_duration_current_week
sensor.living_room_tv_duration_current_month
sensor.barber_duration_last_35_days
```

### 13.3 Session sensors

- Session count for each selected period.
- Last completed session duration.
- Last completed session start timestamp.
- Last completed session end timestamp.
- Days since last completed session.
- First activity time for the current day.
- Last activity time for the current day.

Example barber entities:

```text
sensor.barber_sessions_last_35_days
sensor.barber_duration_last_35_days
sensor.barber_last_session_duration
sensor.barber_last_session_start
sensor.barber_last_session_end
sensor.barber_days_since_last_session
```

For session-count periods, count sessions whose start timestamp belongs to the period. A session that started before the period and continued into it contributes duration but not a new session count.

### 13.4 Comparison sensors

Optional metrics:

- Previous equivalent calendar period.
- Absolute difference.
- Percentage change.

If the previous value is zero, percentage change must be unavailable rather than infinite. Include current and previous absolute values as attributes.

### 13.5 Weekday analysis sensors

The weekday with the highest **total accumulated duration** across the full retained valid history.

This is intentionally based on total, not average.

Expose supporting attributes so unequal weekday occurrence counts remain visible:

```yaml
monday:
  total_seconds: 78120
  observed_days: 10
saturday:
  total_seconds: 148680
  observed_days: 9
analysis_start: "2026-05-29"
analysis_end: "2026-08-26"
partial_days_excluded: 1
```

Possible sensors:

- Weekday with highest total activity.
- Distribution by weekday.
- Total activity on weekdays.
- Total activity on weekends.

All retained history is used for this analysis. Partial days are excluded when completeness is required.

### 13.6 Data quality sensors

Optional sensors:

- Observation coverage percentage.
- Unknown duration.
- Estimated duration.

Example attributes:

```yaml
observed_seconds: 61200
unknown_seconds: 7200
coverage_percentage: 89.47
```

### 13.7 Foreground application sensors

Possible monitor-level sensors:

- Current foreground application.
- Most-used application for a selected period.
- Application count for a selected period.
- Application switch count.
- Top applications ranking as attributes.
- Total tracked foreground-application duration.

Possible application-specific sensors selected by the user:

```text
sensor.igor_phone_youtube_duration_today
sensor.igor_phone_youtube_duration_current_week
sensor.igor_phone_youtube_duration_current_month
```

Do not call aggregate application time definitive screen time unless the source also guarantees screen-on state. Prefer a label such as `Estimated screen activity` when appropriate.

## 14. Barber scenario acceptance example

### 14.1 Configuration

```yaml
name: Barber
monitor_type: zone
entity_id: person.igor
zone_entity_id: zone.barber
retention_days: 90
minimum_session_seconds: 300
merge_gap_seconds: 120
periods:
  - rolling_days: 35
enabled_metrics:
  - session_count
  - total_duration
  - last_session_duration
  - last_session_start
  - last_session_end
  - days_since_last_session
```

### 14.2 Expected results

If two valid visits began in the last 35 calendar days:

```yaml
sensor.barber_sessions_last_35_days:
  state: 2
  attributes:
    period_days: 35
    period_start: "2026-07-23T00:00:00-03:00"
    period_end: "2026-08-26T23:59:59-03:00"
```

Latest visit:

```yaml
sensor.barber_last_session_duration:
  state: 4500
  attributes:
    started_at: "2026-08-20T14:10:00-03:00"
    ended_at: "2026-08-20T15:25:00-03:00"
    formatted: "1h 15min"
    quality: exact
```

Activity Tracker supplies the duration. A template or automation may infer the probable service:

```text
up to 35 minutes -> beard
36 to 60 minutes -> haircut
more than 60 minutes -> haircut and beard
```

That inference is deliberately outside the MVP core.

## 15. Config Flow

Suggested flow:

### Step 1: Monitor type

Options:

- Entity active states.
- Person or device in zone.
- Person in area.
- Foreground application.
- Generic state monitor.

### Step 2: Source

Fields depend on monitor type.

Entity/generic:

- Source entity.
- Active states.

Zone:

- `person` or `device_tracker`.
- Zone.

Area:

- Person.
- Area.
- Presence binary sensor.

Application:

- Source entity.
- State or attribute.
- Value attribute when applicable.
- Optional display-label attribute.

The UI should show known recent states/attributes as suggestions while allowing manual state input where applicable.

### Step 3: Session behavior

- Minimum session duration.
- Unavailable behavior.
- Unavailable tolerance.
- Merge gap.

### Step 4: Retention and history

- Retention in days, initially 90.
- Whether to import available Recorder history.
- If importing, display the available source-history range before confirmation when practical.

### Step 5: Periods

- Today.
- Current week.
- Current month.
- One or more custom rolling-day values.

### Step 6: Metrics/entities

The user explicitly selects every desired metric. Validate at least one selection.

### Step 7: Review

Show a concise summary of source, active rule, periods, retention, and entity count before creation.

## 16. Options Flow

Options Flow must allow:

- Rename monitor.
- Change icon if supported.
- Enable or disable metric entities.
- Add or remove periods.
- Change retention.
- Change minimum session duration.
- Change unavailable behavior and tolerance.
- Change merge gap.
- Change source and active states.
- Manage discovered foreground applications.
- Clear monitor history.
- Reimport Recorder history.

### 16.1 Rule-changing options

Changing source entity, active states, minimum duration, zone, area source, or application extraction can invalidate previous summaries.

The UI must ask:

1. **Keep history:** preserve summaries and apply the new rule only to future activity.
2. **Clear history:** delete summaries and begin a partial day now.
3. **Reimport:** rebuild the available Recorder range using the new rule.

Pure presentation changes such as display name, icon, or enabled entities do not require this prompt.

Daily summaries should include `rule_version`. If history is kept after a rule change, relevant sensor attributes should indicate mixed rule versions.

## 17. Recorder import

Recorder is an optional bootstrap/rebuild source, not the permanent source of truth after consolidation.

### 17.1 Import requirements

- Respect configured retention.
- Discover and present Recorder's available range when possible.
- Reconstruct sessions from state transitions.
- Apply active states, minimum duration, midnight splitting, and session-start counting rules.
- Support state or selected attribute history for foreground applications where Recorder data permits.
- Mark incomplete boundary days as partial.
- Mark reconstructed data quality appropriately, for example `estimated` or `imported`.
- Execute asynchronously without blocking Home Assistant startup.
- Report progress and completion through config-entry state or disabled-by-default diagnostic entities.
- Be idempotent.

### 17.2 Reimport behavior

- Replace reconstructed daily ranges instead of adding to them.
- Preserve older retained summaries that are no longer present in Recorder.
- Apply the current rule to reimported days.
- Report rebuilt days, preserved days, processed transitions/sessions, and warnings.

Example result:

```yaml
status: completed
range_start: "2026-08-16"
range_end: "2026-08-26"
days_rebuilt: 11
days_preserved: 48
sessions_processed: 37
warnings: 1
```

## 18. Administrative actions

The MVP must expose these actions through Options Flow or integration actions:

### 18.1 Clear history

- Require explicit confirmation.
- Delete all daily summaries and last completed-session metadata.
- Reset or safely restart the active checkpoint.
- Begin a partial day at the operation timestamp.
- Keep config entry and selected entities.

### 18.2 Reimport from Recorder

- Require confirmation when existing summaries will be replaced.
- Run asynchronously.
- Prevent concurrent import/cleanup conflicts.

CSV/JSON export and repair tools are deferred beyond the MVP.

## 19. Entity availability and diagnostics

Sensors must use `unavailable` when their contract cannot be satisfied, including:

- Insufficient complete history for the configured rolling period.
- Retention shorter than the requested period.
- Missing source entity.
- Invalid source attribute.
- Storage migration or corruption that prevents a reliable result.

Where useful, include machine-readable attributes:

```yaml
reason: insufficient_history
required_days: 35
available_days: 18
```

Diagnostic information should include:

- Monitor type.
- Source entity ID.
- Rule version.
- Retention.
- Oldest/newest stored date.
- Current checkpoint status.
- Last successful import.
- Last cleanup.
- Count of stored daily summaries.

Diagnostics and logs must not dump full location/application history or other sensitive data.

## 20. Update scheduling and events

Recalculate affected entities on:

- Source state change.
- Source relevant attribute change.
- Session start/end.
- Foreground application change.
- Once per minute while a session is active.
- Local midnight.
- Week/month boundary as applicable.
- Import completion.
- Cleanup completion.
- Options update.
- Home Assistant startup.

Avoid per-second updates and unnecessary Recorder state growth.

## 21. Time and calendar rules

- Use timezone-aware datetimes everywhere.
- Use Home Assistant's configured timezone.
- Split sessions at local midnight.
- Correctly handle daylight-saving transitions even if uncommon in the user's current locale.
- Derive week/month/date keys from HA-local time, not UTC dates.
- Store canonical timestamps in a format safe for migration and timezone interpretation.
- Do not manually assume every local day has exactly 86,400 seconds.

## 22. Entity and device registry behavior

- One config entry creates one virtual device.
- All selected entities for the monitor attach to that device.
- Unique IDs must be based on config entry ID plus stable metric/period identifiers, not mutable display names.
- Disabling a metric should use normal Home Assistant entity-registry behavior where possible.
- Renaming the monitor or application label must not change unique IDs.
- Removing the config entry removes its entities and stored data.

Suggested unique-ID pattern:

```text
<entry_id>_<metric>_<period_key>
```

Examples:

```text
abc123_total_duration_current_day
abc123_session_count_rolling_35_days
abc123_last_session_duration
```

## 23. Suggested implementation structure

Conceptual package layout:

```text
custom_components/activity_tracker/
  __init__.py
  manifest.json
  const.py
  config_flow.py
  coordinator.py
  models.py
  session_engine.py
  storage.py
  recorder_import.py
  periods.py
  sensor.py
  binary_sensor.py
  diagnostics.py
  services.yaml
  strings.json
  translations/en.json
```

Suggested responsibilities:

- `models.py`: typed configuration, checkpoint, daily summary, application aggregate, and last-session models.
- `session_engine.py`: pure session transition logic and midnight splitting.
- `periods.py`: timezone-aware calendar and rolling period calculations.
- `storage.py`: versioned persistence, atomic updates, retention, migrations.
- `recorder_import.py`: asynchronous reconstruction from Recorder.
- `coordinator.py`: runtime observation and entity refresh scheduling.
- `sensor.py` / `binary_sensor.py`: Home Assistant entities only; avoid embedding session logic here.
- `config_flow.py`: creation, options, validation, reauthentication-style progress steps if needed for import.

The core session engine should be as pure and deterministic as possible to make boundary-condition testing straightforward.

## 24. Data model versioning

Storage must declare a schema version from the first release.

Example:

```yaml
storage_version: 1
```

Migrations must be transactional where practical. If a migration fails, preserve the previous data and mark the entry unavailable rather than silently resetting history.

## 25. Testing requirements

### 25.1 Session engine tests

- Inactive to active starts one session.
- Active to active does not split a session.
- Active to inactive ends one session.
- Duplicate source events do not duplicate sessions.
- Application A to application B creates two application sessions.
- Minimum-duration session accepted.
- Below-minimum session discarded.
- Minimum-duration session crossing midnight is evaluated as a complete session.
- Session crossing midnight splits duration but counts start only on the first day.
- Session crossing week and month boundaries aggregates correctly.
- Merge gap joins activity without counting inactive gap duration.
- Gap beyond threshold creates a new session.
- Unavailable tolerance behavior is respected.

### 25.2 Time tests

- Local midnight boundary.
- DST short day.
- DST long day.
- Month boundary.
- Year boundary.
- Configured week boundary.
- Rolling 35 calendar days.
- First partial day excluded from complete-history analytics.

### 25.3 Restart tests

- Restart during active session.
- Restart during below-minimum pending session.
- Restart during merge gap.
- Downtime marked unknown.
- Current active state after restart resumes safely without double counting.

### 25.4 Storage tests

- Atomic save/load.
- Storage schema migration.
- Retention cleanup.
- Config-entry removal cleanup.
- Corrupt or incomplete data handling.
- App aggregates remain isolated by monitor/device.

### 25.5 Import tests

- Import active/inactive history.
- Import selected state attribute history when available.
- Import partial boundary days.
- Idempotent reimport.
- Preserve dates outside Recorder range.
- Apply current rule version.
- Cancel or recover failed import without corrupting summaries.

### 25.6 Entity tests

- Only user-selected entities are created.
- Stable unique IDs after rename.
- Duration native units and device classes are valid.
- Rolling sensor unavailable until sufficient history.
- Current calendar sensor available immediately.
- Percentage comparison handles zero correctly.
- Last-session sensor survives restart.

### 25.7 Config Flow tests

- All five monitor types.
- Source entity filters.
- Manual active-state entry.
- Attribute selection for applications.
- At least one metric required.
- Retention/period validation.
- Keep, clear, and reimport choices after rule changes.
- Delete warning and cleanup.

## 26. MVP acceptance criteria

The MVP is complete when all of the following are true:

1. A user can create each supported monitor type entirely through the UI.
2. Every monitor is represented by a separate config entry and virtual device.
3. The user explicitly selects periods and sensors during creation.
4. Activity remains correct across active-state transitions, midnight, and Home Assistant restarts.
5. Daily summaries are stored independently of Recorder retention.
6. Retention cleanup works per monitor with a 90-day default.
7. Current day/week/month and custom rolling-day sensors work according to completeness rules.
8. Session counts use session start dates and do not double-count midnight continuations.
9. Last completed-session duration/start/end are available without retaining full session history.
10. Zone monitors work with `person` and `device_tracker` for one selected zone.
11. Area monitors use an explicit person-area binary sensor.
12. Foreground application monitors read from state or one selected attribute and remain separated per device.
13. Recorder history can optionally initialize or rebuild summaries.
14. Rule changes offer keep, clear, or reimport behavior.
15. Clear-history and reimport actions are available.
16. The barber scenario works with a configurable 35-calendar-day session count and last-session duration.
17. Automated tests cover session, time, restart, storage, import, entity, and flow behavior.

## 27. Future evolution

Potential later versions may add:

- Custom dashboard with cards, timelines, charts, and heatmaps.
- Temporary detailed-session retention and manual session correction.
- Grouped monitors and rankings across devices, zones, or areas.
- Area-most-visited and device-most-used aggregators.
- Numeric and attribute-based generic rules.
- Multiple-entity conditions.
- Foreground plus background-media activity.
- Native mobile collectors for screen/application activity.
- Configurable duration-to-label inference.
- Goals and alerts, such as maximum TV time or minimum gym time.
- CSV/JSON export.
- Data repair tools.
- More translations beyond English and Brazilian Portuguese.
- Long-term aggregate tiers beyond detailed daily retention.

## 28. Important implementation cautions

- A network-connected phone is not necessarily being used, and a foreground-app value is not always definitive screen-on evidence. Entity names and documentation must avoid overstating what the source proves.
- GPS and radio-based zone/area data can oscillate. Minimum duration, unavailable tolerance, and merge gap are core correctness features, not optional polish.
- Do not query Recorder repeatedly for normal sensor updates. Recorder is only an import/rebuild source.
- Do not store historical sessions accidentally through verbose checkpoints or logs.
- Do not use mutable names as persistence or entity identifiers.
- Do not assume 24-hour days when splitting local calendar time.
- Do not silently mix rule versions without exposing that fact in sensor attributes or diagnostics.
- Do not calculate a complete rolling-period result from partial history; expose `unavailable` and the missing coverage.
