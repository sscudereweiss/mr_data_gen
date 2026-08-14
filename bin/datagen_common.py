"""Shared helpers for mr_data_gen scripted inputs."""

from __future__ import annotations

import configparser
import csv
import os
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


def spl_random() -> int:
    """Match Splunk random() range used in datagen macros."""
    import random

    return random.randint(0, 2147483647)


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


def format_raw_line(host: str, raw: str) -> str:
    return f"_MetaData:Host::{host}\n{raw}"
