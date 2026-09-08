# Changelog

All user-relevant changes are documented in this file.

## [2026.9.0] - 2026-09-08

### Added

- Added the **Mobile device in use** monitor for Android devices using the Home
  Assistant Companion App. Setup selects one device and automatically validates
  its required Interactive and Last update trigger entities.

### Fixed

- Mobile screen-use sessions now stop or follow the configured unavailable-source
  behavior after the phone stops communicating, preventing a drained battery or
  lost connection from leaving an old interactive state active indefinitely.

## [2026.8.1] - 2026-08-27

### Changed

- Improved activity accounting across brief interruptions and unavailable sources.
- Corrected zone monitors to recognize the `home` and named-zone states reported
  by person and device-tracker entities.
- Added a per-monitor duration display format: hours, minutes, or seconds.
  New monitors default to hours, while existing monitors retain seconds until
  edited.

## [2026.8.0] - 2026-08-26

### Added

- Initial Activity Tracker integration with UI monitor setup, persistent daily activity summaries, and selectable sensor metrics.
- Added clearer setup guidance, field descriptions, readable selector labels, and validation for rolling-day values.
