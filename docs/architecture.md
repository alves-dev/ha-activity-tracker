# Storage and entity behavior

Every monitor owns `.storage/activity_tracker.<config-entry-id>`. It contains one aggregate per local date, a small active-session checkpoint, and latest-completed-session metadata. Detailed completed session history is intentionally not retained.

Activity duration is internally calculated in seconds. Duration sensors expose numeric seconds with Home Assistant's duration device class. Rolling days refer to local calendar dates, not exact 24-hour intervals.

Recorder import and destructive history rebuild are intentionally deferred; the options model reserves the behavior settings without making false historical claims.
