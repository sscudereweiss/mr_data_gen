"""EDU DC1 metric generation library — backward-compatible wrapper around dc_metrics_lib."""

from __future__ import annotations

from typing import Iterable, Optional
from datetime import datetime
import configparser

from dc_metrics_lib import (  # noqa: F401 — re-export for callers
    apply_metrics,
    build_dimensions,
    build_host_payload,
    get_app_dir,
    in_demo_window,
    load_hosts,
    load_settings as _load_settings,
    spl_random,
)

CONFIG_NAME = "edu_dc1"


def load_settings(app_dir=None) -> configparser.ConfigParser:
    return _load_settings(CONFIG_NAME, app_dir=app_dir)


def iter_host_lines(
    settings: Optional[configparser.ConfigParser] = None,
    now: Optional[datetime] = None,
) -> Iterable[str]:
    from dc_metrics_lib import iter_host_lines as _iter_host_lines

    return _iter_host_lines(CONFIG_NAME, settings=settings, now=now)
