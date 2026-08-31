"""Constants for Activity Tracker."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "activity_tracker"
INTEGRATION_NAME = "Activity Tracker"
INTEGRATION_VERSION = "2026.8.1"
PLATFORMS = (Platform.BINARY_SENSOR, Platform.SENSOR)

CONF_MONITOR_TYPE = "monitor_type"
CONF_ENTITY_ID = "entity_id"
CONF_ACTIVE_STATES = "active_states"
CONF_ZONE_ENTITY_ID = "zone_entity_id"
CONF_PERSON_ENTITY_ID = "person_entity_id"
CONF_AREA_ID = "area_id"
CONF_PRESENCE_ENTITY_ID = "presence_entity_id"
CONF_VALUE_SOURCE = "value_source"
CONF_VALUE_ATTRIBUTE = "value_attribute"
CONF_LABEL_ATTRIBUTE = "label_attribute"
CONF_NAME = "name"
CONF_PERIODS = "periods"
CONF_PERIOD_METRICS = "period_metrics"
CONF_ENABLED_METRICS = "enabled_metrics"

TYPE_ENTITY_STATE = "entity_state"
TYPE_ZONE = "zone"
TYPE_AREA_PRESENCE = "area_presence"
TYPE_FOREGROUND_APPLICATION = "foreground_application"
TYPE_GENERIC = "generic"
MONITOR_TYPES = (
    TYPE_ENTITY_STATE,
    TYPE_ZONE,
    TYPE_AREA_PRESENCE,
    TYPE_FOREGROUND_APPLICATION,
    TYPE_GENERIC,
)

PERIOD_TODAY = "current_day"
PERIOD_WEEK = "current_week"
PERIOD_MONTH = "current_month"
PERIODS = (PERIOD_TODAY, PERIOD_WEEK, PERIOD_MONTH)

METRIC_TOTAL_DURATION = "total_duration"
METRIC_SESSION_COUNT = "session_count"
METRIC_CURRENT_SESSION_DURATION = "current_session_duration"
METRIC_LAST_SESSION_DURATION = "last_session_duration"
METRIC_LAST_SESSION_START = "last_session_start"
METRIC_LAST_SESSION_END = "last_session_end"
METRIC_DAYS_SINCE_LAST_SESSION = "days_since_last_session"
METRIC_AVERAGE_DAILY_DURATION = "average_daily_duration"
METRIC_AVERAGE_SESSION_DURATION = "average_session_duration"
METRIC_LONGEST_SESSION_DURATION = "longest_session_duration"
METRIC_SHORTEST_SESSION_DURATION = "shortest_session_duration"
METRIC_FIRST_ACTIVITY_TIME = "first_activity_time"
METRIC_LAST_ACTIVITY_TIME = "last_activity_time"
METRIC_WEEKDAY_MAX = "weekday_highest_total"
METRIC_UNKNOWN_DURATION = "unknown_duration"
METRICS = (
    METRIC_TOTAL_DURATION,
    METRIC_SESSION_COUNT,
    METRIC_CURRENT_SESSION_DURATION,
    METRIC_LAST_SESSION_DURATION,
    METRIC_LAST_SESSION_START,
    METRIC_LAST_SESSION_END,
    METRIC_DAYS_SINCE_LAST_SESSION,
    METRIC_AVERAGE_DAILY_DURATION,
    METRIC_AVERAGE_SESSION_DURATION,
    METRIC_LONGEST_SESSION_DURATION,
    METRIC_SHORTEST_SESSION_DURATION,
    METRIC_FIRST_ACTIVITY_TIME,
    METRIC_LAST_ACTIVITY_TIME,
    METRIC_WEEKDAY_MAX,
    METRIC_UNKNOWN_DURATION,
)

PERIOD_METRICS = frozenset(
    {
        METRIC_TOTAL_DURATION,
        METRIC_SESSION_COUNT,
        METRIC_AVERAGE_DAILY_DURATION,
        METRIC_AVERAGE_SESSION_DURATION,
        METRIC_LONGEST_SESSION_DURATION,
        METRIC_SHORTEST_SESSION_DURATION,
        METRIC_UNKNOWN_DURATION,
    }
)
NON_PERIOD_METRICS = tuple(metric for metric in METRICS if metric not in PERIOD_METRICS)

OPT_RETENTION_DAYS = "retention_days"
OPT_MINIMUM_SESSION_SECONDS = "minimum_session_seconds"
OPT_UNAVAILABLE_BEHAVIOR = "unavailable_behavior"
OPT_UNAVAILABLE_TOLERANCE_SECONDS = "unavailable_tolerance_seconds"
OPT_MERGE_GAP_SECONDS = "merge_gap_seconds"
OPT_IMPORT_RECORDER_HISTORY = "import_recorder_history"
OPT_DURATION_UNIT = "duration_unit"

DEFAULT_RETENTION_DAYS = 90
DEFAULT_MINIMUM_SESSION_SECONDS = 0
DEFAULT_UNAVAILABLE_BEHAVIOR = "unknown"
DEFAULT_UNAVAILABLE_TOLERANCE_SECONDS = 0
DEFAULT_MERGE_GAP_SECONDS = 0
DEFAULT_DURATION_UNIT = "h"
DURATION_UNITS = ("s", "min", "h")


def update_signal(entry_id: str) -> str:
    """Return the runtime update signal for an entry."""
    return f"{DOMAIN}_{entry_id}_updated"
