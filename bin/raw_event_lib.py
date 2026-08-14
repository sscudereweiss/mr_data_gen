"""Raw event generation for MySQL and Nagios scripted inputs."""

from __future__ import annotations

import configparser
from datetime import datetime
from typing import Iterable, Optional

from datagen_common import (
    format_raw_line,
    in_demo_window,
    in_minute_window,
    load_settings,
    now_in_tz,
)


def mysql_logcount(minute: int) -> int:
    return round(minute * 2 / 10)


def build_mysql_logline(now: datetime) -> str:
    stamp = now.strftime("%Y/%m/%d %H:%M:%S")
    return (
        f"{stamp} [CRITICAL] /opt/mysql/bin/mysqld: Disk is full writing "
        "'/mysqllog/binlog/localhost-3306-bin.000020' (Errcode: 28). "
        "Waiting for someone to free space... Retry in 60 secs"
    )


def build_nagios_logline(now: datetime, host: str, minute: int) -> str:
    ts = now.timestamp()
    return (
        f"[SERVICEPERFDATA]\t{ts}\t{host}\tHost Unavailable {minute} - Ping \t"
        f"0\t0\tPING CRITICAL - Packet loss = 100%, RTA = 0 ms\trta=0ms;"
        f"0.000000;0.000000;0.000000 pl=0%;2;5;0"
    )


def _host_suffix(index: int) -> str:
    return str(index)


def _iter_mysql_lines(settings: configparser.ConfigParser, now: datetime) -> Iterable[str]:
    host_prefix = settings.get("settings", "host_prefix")
    host_count = int(settings.get("settings", "host_count", fallback="4"))
    minute = int(now.strftime("%M"))
    logcount = mysql_logcount(minute)
    logline = build_mysql_logline(now)

    for idx in range(1, host_count + 1):
        host = f"{host_prefix}{idx:02d}"
        for _ in range(logcount):
            yield format_raw_line(host, logline)


def _iter_nagios_lines(settings: configparser.ConfigParser, now: datetime) -> Iterable[str]:
    host_prefix = settings.get("settings", "host_prefix")
    events_per_run = int(settings.get("settings", "events_per_run", fallback="5"))
    minute = int(now.strftime("%M"))

    for event_idx in range(1, events_per_run + 1):
        count = (event_idx % 4) + 1
        host = f"{host_prefix}{count}"
        yield format_raw_line(host, build_nagios_logline(now, host, minute))


def iter_raw_event_lines(
    config_name: str,
    settings: Optional[configparser.ConfigParser] = None,
    now: Optional[datetime] = None,
) -> Iterable[str]:
    settings = settings or load_settings(config_name)
    now = now_in_tz(settings, now)

    if not in_demo_window(settings, now):
        return
    if not in_minute_window(settings, now):
        return

    generator_type = settings.get("settings", "generator_type", fallback="mysql")
    if generator_type == "mysql":
        yield from _iter_mysql_lines(settings, now)
    elif generator_type == "nagios":
        yield from _iter_nagios_lines(settings, now)
    else:
        raise ValueError(f"unsupported generator_type={generator_type!r}")
