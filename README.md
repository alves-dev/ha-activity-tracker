# Activity Tracker

<p align="center">
  <img src="docs/activity-tracker-logo.png" alt="Activity Tracker logo" width="320">
</p>

[![Quality Gate](https://sonar.alves-dev.com/api/project_badges/measure?project=ha-activity-tracker&metric=alert_status)](https://sonar.alves-dev.com/dashboard?id=ha-activity-tracker)
[![Coverage](https://sonar.alves-dev.com/api/project_badges/measure?project=ha-activity-tracker&metric=coverage)](https://sonar.alves-dev.com/dashboard?id=ha-activity-tracker)
![Version](https://img.shields.io/badge/Version-2026.9.1-41BDF5?style=flat-square)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.8%2B-41BDF5?logo=homeassistant)

Track activities in Home Assistant with one composable start rule and one
composable stop rule. Activity Tracker observes source reports live and stores
compact daily summaries independently of Recorder.

## Features

- A guided **Zone presence** template and a fully custom rule editor.
- State, state-for-duration, and no-report-for-duration conditions.
- AND/OR expressions, including `(A and B) or (C and D)`.
- Explicit `unavailable` and `unknown` stop conditions. A delayed source-health
  condition confirms at its deadline but stops accounting at the first bad
  observation.
- Per-monitor retention, minimum completed duration, and seconds/minutes/hours
  presentation; hours are the default.
- Today, current week, current month, and closed historical days. **Last 1** is
  yesterday; **Last 2** is the day before yesterday.
- Average local start/end times, calculated circularly so times around midnight
  average correctly.
- A selectable cross-midnight policy: started day, ended day, or split at local
  midnight. Split sessions contribute one session to every participating day.

The current-day total-duration sensor is a daily `total_increasing` counter;
Home Assistant records it as `sum` statistics for a daily graph. Other report
totals are measurements.

## HACS availability

Activity Tracker is a HACS custom repository (Integration category), not
available in the default HACS catalog. Add
`https://github.com/alves-dev/ha-activity-tracker` in HACS, install it, and
restart Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=alves-dev&repository=ha-activity-tracker&category=integration)

## Install

Install the custom repository from HACS and restart Home Assistant.

## Configure

Add **Activity Tracker** from *Settings → Devices & services → Add integration*.
Choose **Zone presence** to track a person/device tracker in a selected zone, or
choose **Custom rule** to build start and stop expressions. After every custom
condition, the flow shows the accumulated expression; choose AND, OR, or finish.

Choose at least one report period and one metric for every selected period.
Monitor-wide metrics, such as current-session duration and time since the latest
session, are optional. Editing a rule or cross-midnight policy asks for explicit
confirmation before clearing incompatible retained summaries. There is no
configuration, entity, storage, or Recorder-history migration from prior
Activity Tracker releases.

## Technical documentation

- [Storage and sensor contract](docs/architecture.md)
- [Compatibility](docs/compatibility.md)
- [Development and validation](docs/development.md)

## License

MIT. See [LICENSE](LICENSE).
