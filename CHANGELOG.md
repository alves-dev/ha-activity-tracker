# Changelog

All user-relevant changes are documented in this file.

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
