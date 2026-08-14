"""Shared metric generation library for mr_data_gen scripted inputs."""

from __future__ import annotations

import configparser
import json
from datetime import datetime
from typing import Any, Dict, Iterable, Optional, Set

from datagen_common import (
    get_app_dir,
    get_bool,
    get_csv_set,
    in_demo_window,
    load_csv_lookup,
    load_settings,
    now_in_tz,
    spl_random,
)


def load_hosts(
    lookup_name: str,
    app_dir: Optional[str] = None,
    enabled_only: bool = True,
    host_filter: Optional[Set[str]] = None,
):
    return load_csv_lookup(
        lookup_name=lookup_name,
        app_dir=app_dir,
        enabled_only=enabled_only,
        host_filter=host_filter,
    )


def build_dimensions(row: Dict[str, str], os_version: str) -> Dict[str, str]:
    profile = row["profile"]
    if profile == "windows":
        return {"entity_type": "Windows", "instance": "_Total"}
    return {
        "os": "Linux",
        "os_version": os_version,
        "entity_type": "nix",
        "process_name": "system",
        "role": row["role"],
        "ip": row["ip"],
    }


def apply_metrics(row: Dict[str, str], minute: int, metric_filter: Optional[Set[str]] = None) -> Dict[str, Any]:
    """Port of local/macros.conf edu_dc1_apply_metrics."""
    profile = row["profile"]
    metrics: Dict[str, Any] = {}

    def add(name: str, value: Any) -> None:
        if value is None:
            return
        if metric_filter and name not in metric_filter:
            return
        metrics[f"metric_name:{name}"] = value

    if profile != "windows":
        if profile == "unstable" and minute > 39 and minute < 60:
            processmon = spl_random() % 15 + 85
        else:
            processmon = spl_random() % 25 + 40
        add("processmon.cpu.percent", processmon)

        interrupt = spl_random() % 5000 / 100000
        nice = round(0, 2)
        softriq = spl_random() % 5000 / 100000
        steal = round(0, 2)
        system = processmon * (1 / 10)
        user = processmon * (9 / 10)
        wait = spl_random() % 5000 / 100000
        idle = 100 - interrupt - nice - softriq - steal - system - user - wait

        add("cpu.interrupt", interrupt)
        add("cpu.nice", nice)
        add("cpu.softriq", softriq)
        add("cpu.steal", steal)
        add("cpu.system", system)
        add("cpu.user", user)
        add("cpu.wait", wait)
        add("cpu.idle", idle)

        reserved = spl_random() % 10
        if profile == "unstable" and minute > 37 and minute < 60:
            df_used = spl_random() % 10 + 90
        else:
            df_used = spl_random() % 10 + 50
        add("df.reserved", reserved)
        add("df.used", df_used)
        add("df.free", 100 - reserved - df_used)

        add("disk.io_time.io_time", spl_random() % 6000 + 2000)
        add("disk.io_time.weighted_io_time", spl_random() % 21000 + 4000)
        add("disk.merged.read", 0)
        add("disk.merged.write", spl_random() % 100 + 40)
        add("disk.octets.read", spl_random() % 1000 + 500)
        add("disk.octets.write", spl_random() % 1000 + 500)
        add("disk.ops.read", spl_random() % 50000 / 100 + 1800.00)
        add("disk.ops.write", spl_random() % 50000 / 100 + 1800.00)
        add("disk.time.read", (spl_random() % 400 + 400) / 1000)
        add("disk.time.write", (spl_random() % 1000 + 2000) / 1000)

        add("memory.buffered", spl_random() % 10 / 100000)
        add("memory.cached", spl_random() % 10 / 100000)
        add("memory.slab_recl", spl_random() % 500 / 100)
        add("memory.slab_unrecl", round(0, 2))
        if profile == "unstable" and minute > 37 and minute < 60:
            memory_used = spl_random() % 10 + 90
        else:
            memory_used = spl_random() % 10 + 50
        add("memory.used", memory_used)
        add("memory.free", 100 - memory_used)

        add("interface.dropped.rx", 0)
        add("interface.dropped.tx", 0)
        add("interface.errors.rx", 0)
        add("interface.errors.tx", 0)
        add("interface.octets.rx", spl_random() % 500000 + 500000)
        add("interface.octets.tx", spl_random() % 1500000 + 1500000)
        add("interface.packets.rx", spl_random() % 700000000 / 100 + 1)
        add("interface.packets.tx", spl_random() % 200000000 / 100 + 1)

    if profile == "windows":
        add("Processor.%_Idle_Time", spl_random() % 25 + 40)
        add("Memory.%_Committed_Bytes_In_Use", spl_random() % 10 + 60)
        add("LogicalDisk.%_Free_Space", spl_random() % 10 + 50)
        add("Avg._Disk_Bytes/Read", spl_random() % 50000 / 100 + 1800.00)
        add("Avg._Disk_Bytes/Write", spl_random() % 50000 / 100 + 1800.00)
        add("Network_Interface.Bytes_Received/sec", spl_random() % 700000000 / 100 + 1)
        add("Network_Interface.Bytes_Sent/sec", spl_random() % 200000000 / 100 + 1)

    return metrics


def build_host_payload(
    row: Dict[str, str],
    os_version: str,
    minute: int,
    metric_filter: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    payload = apply_metrics(row, minute, metric_filter=metric_filter)
    payload.update(build_dimensions(row, os_version))
    payload["index_host"] = row["host"]
    return payload


def iter_host_lines(
    config_name: str,
    settings: Optional[configparser.ConfigParser] = None,
    now: Optional[datetime] = None,
) -> Iterable[str]:
    """Yield indexing-optimized stdout lines for the scripted input."""
    settings = settings or load_settings(config_name)
    now = now_in_tz(settings, now)

    if not in_demo_window(settings, now):
        return

    app_dir = get_app_dir()
    lookup_name = settings.get("settings", "hosts_lookup", fallback=f"{config_name}_hosts.csv")
    os_version = settings.get("settings", "os_version", fallback="2.6.32-573.8.1.el6.x86_64")
    minute = int(now.strftime("%M"))

    spike_enabled = get_bool(settings, "spike", "enabled", False)
    host_filter = get_csv_set(settings, "spike", "hosts") if spike_enabled else set()
    metric_filter = get_csv_set(settings, "spike", "metrics") if spike_enabled else set()

    hosts = load_hosts(
        lookup_name=lookup_name,
        app_dir=app_dir,
        enabled_only=True,
        host_filter=host_filter or None,
    )

    for row in hosts:
        payload = build_host_payload(row, os_version, minute, metric_filter or None)
        yield json.dumps(payload, separators=(",", ":"), sort_keys=True)
