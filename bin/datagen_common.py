"""Shared helpers for mr_data_gen scripted inputs."""

from __future__ import annotations

import configparser
import csv
import os
import socket
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set
from zoneinfo import ZoneInfo

DAY_MAP = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


@dataclass
class RunContext:
    run_id: str
    skip_reason: str
    expected_output_count: int
    now: datetime
    demo_window_active: bool
    minute_window_active: bool


def spl_random() -> int:
    """Match Splunk random() range used in datagen macros."""
    import random

    return random.randint(0, 2147483647)


def mysql_logcount(minute: int) -> int:
    return round(minute * 2 / 10)


def get_app_dir() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_candidate = os.path.dirname(script_dir)
    if os.path.isdir(os.path.join(repo_candidate, "lookups")):
        return repo_candidate

    splunk_home = os.environ.get("SPLUNK_HOME", "/opt/splunk")
    return os.path.join(splunk_home, "etc", "apps", "mr_data_gen")


def load_settings(
    config_name: str,
    app_dir: Optional[str] = None,
) -> configparser.ConfigParser:
    app_dir = app_dir or get_app_dir()
    parser = configparser.ConfigParser()
    for path in (
        os.path.join(app_dir, "default", f"{config_name}_datagen.conf"),
        os.path.join(app_dir, "local", f"{config_name}_datagen.conf"),
        os.path.join(app_dir, "local", "observability_common.conf"),
    ):
        if os.path.isfile(path):
            parser.read(path)
    return parser


def get_bool(parser: configparser.ConfigParser, section: str, option: str, default: bool) -> bool:
    if not parser.has_option(section, option):
        return default
    return parser.get(section, option).strip().lower() in ("1", "true", "yes", "on")


def get_csv_set(parser: configparser.ConfigParser, section: str, option: str) -> Set[str]:
    if not parser.has_option(section, option):
        return set()
    raw = parser.get(section, option).strip()
    if not raw:
        return set()
    return {item.strip() for item in raw.split(",") if item.strip()}


def load_csv_lookup(
    lookup_name: str,
    app_dir: Optional[str] = None,
    enabled_only: bool = True,
    host_filter: Optional[Set[str]] = None,
) -> List[Dict[str, str]]:
    app_dir = app_dir or get_app_dir()
    lookup_path = os.path.join(app_dir, "lookups", lookup_name)
    rows: List[Dict[str, str]] = []
    with open(lookup_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if enabled_only and row.get("enabled", "1") != "1":
                continue
            if host_filter and row.get("host") not in host_filter:
                continue
            rows.append(row)
    return rows


def now_in_tz(settings: configparser.ConfigParser, now: Optional[datetime] = None) -> datetime:
    tz_name = settings.get("settings", "demo_timezone", fallback="America/New_York")
    return now or datetime.now(ZoneInfo(tz_name))


def in_demo_window(settings: configparser.ConfigParser, now: Optional[datetime] = None) -> bool:
    if not get_bool(settings, "settings", "demo_hours_only", True):
        return True

    now = now_in_tz(settings, now)
    start_hour = int(settings.get("settings", "demo_start_hour", fallback="8"))
    end_hour = int(settings.get("settings", "demo_end_hour", fallback="18"))
    if now.hour < start_hour or now.hour > end_hour:
        return False

    demo_days = settings.get("settings", "demo_days", fallback="mon,tue,wed,thu,fri")
    allowed = {DAY_MAP[day.strip().lower()] for day in demo_days.split(",") if day.strip()}
    return now.weekday() in allowed


def in_minute_window(settings: configparser.ConfigParser, now: Optional[datetime] = None) -> bool:
    now = now_in_tz(settings, now)
    minute = int(now.strftime("%M"))
    start = int(settings.get("settings", "demo_minute_start", fallback="0"))
    end = int(settings.get("settings", "demo_minute_end", fallback="59"))
    return start <= minute <= end


def uses_minute_gate(settings: configparser.ConfigParser) -> bool:
    start = int(settings.get("settings", "demo_minute_start", fallback="0"))
    end = int(settings.get("settings", "demo_minute_end", fallback="59"))
    return start != 0 or end != 59


def resolve_skip_reason(settings: configparser.ConfigParser, now: Optional[datetime] = None) -> str:
    now = now_in_tz(settings, now)
    if not in_demo_window(settings, now):
        return "demo_hours"
    if uses_minute_gate(settings) and not in_minute_window(settings, now):
        return "minute_window"
    return "none"


def expected_output_count(
    settings: configparser.ConfigParser,
    config_name: str,
    now: Optional[datetime] = None,
) -> int:
    if resolve_skip_reason(settings, now) != "none":
        return 0

    now = now_in_tz(settings, now)
    generator_type = settings.get("settings", "generator_type", fallback="").strip()

    if generator_type == "mysql":
        host_count = int(settings.get("settings", "host_count", fallback="4"))
        minute = int(now.strftime("%M"))
        return host_count * mysql_logcount(minute)

    if generator_type == "nagios":
        return int(settings.get("settings", "events_per_run", fallback="5"))

    if settings.has_option("settings", "sf_service"):
        return 7

    if settings.has_option("settings", "sf_environment"):
        return 1

    lookup_name = settings.get("settings", "hosts_lookup", fallback=f"{config_name}_hosts.csv")
    return len(load_csv_lookup(lookup_name, enabled_only=True))


def resolve_host_name(settings: configparser.ConfigParser) -> str:
    configured = settings.get("observability", "host_name", fallback="").strip()
    if configured:
        return configured
    return socket.gethostname()


def resolve_service_name(settings: configparser.ConfigParser, config_name: str) -> str:
    default_service = f"mr_data_gen_{config_name}"
    return settings.get("observability", "service_name", fallback=default_service)


def log_correlation_enabled(settings: configparser.ConfigParser) -> bool:
    return get_bool(settings, "observability", "log_correlation", True)


def build_run_context(
    settings: configparser.ConfigParser,
    config_name: str,
    run_id: str,
    now: Optional[datetime] = None,
) -> RunContext:
    now = now_in_tz(settings, now)
    return RunContext(
        run_id=run_id,
        skip_reason=resolve_skip_reason(settings, now),
        expected_output_count=expected_output_count(settings, config_name, now),
        now=now,
        demo_window_active=in_demo_window(settings, now),
        minute_window_active=in_minute_window(settings, now),
    )


def format_raw_line(host: str, raw: str) -> str:
    return f"_MetaData:Host::{host}\n{raw}"
