"""Sim metrics generation for RUM and APM scripted inputs."""

from __future__ import annotations

import configparser
import json
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from datagen_common import (
    in_demo_window,
    load_settings,
    now_in_tz,
    spl_random,
)


def apply_rum_metrics(env: str, minute: int) -> Dict[str, Any]:
    """Port of default/macros.conf rum_metrics(1)."""
    page_views = spl_random() % 100
    spike = minute > 39 and minute < 60

    operationrand = spl_random() % 7
    if minute < 40 and operationrand == 4:
        operationrand = 0

    operations = [
        "HTTP POST",
        "console.error",
        "documentFetch",
        "documentLoad",
        "onerror",
        "resourceFetch",
        "webvitals",
    ]
    sf_operation = operations[operationrand]

    payload: Dict[str, Any] = {
        "metric_name:rum.page_view.count": page_views,
        "metric_name:rum.client_error.count": (
            page_views * (spl_random() % 50) + 10 if spike else 0
        ),
        "metric_name:rum.page_view.time.ns.p75": (
            (spl_random() % 50) + 10 if spike else spl_random() % 5
        ),
        "metric_name:rum.resource_request.count": page_views * (50 + spl_random() % 100),
        "metric_name:rum.webvitals_lcp.time.ns.p75": (
            (spl_random() % 50 + 460) * (50 + spl_random() % 100)
            if spike
            else spl_random() % 50 + 460
        ),
        "metric_name:rum.resource_request.time.ns.p75": (
            (spl_random() % 50) + 10 if spike else spl_random() % 5
        ),
        "metric_name:rum.webvitals_fid.time.ns.p75": (
            (50 + spl_random() % 100) * (spl_random() % 30) + 20
            if spike
            else (spl_random() % 30) + 20
        ),
        "metric_name:rum.webvitals_cls.score.p75": (
            (50 + spl_random() % 100) * spl_random() % 60 / 1000
            if spike
            else spl_random() % 60 / 1000
        ),
        "app": env,
        "computationId": "FskgDsKA4AQ",
        "country": "USA",
        "sf_environment": env,
        "sf_node_type": "provider" if spl_random() % 2 == 0 else "view",
        "sf_operation": sf_operation,
        "sf_organizationID": "FgpBtZ0A0AA",
        "sf_product": "web",
        "sf_realm": "us1",
        "sf_resolutionMs": 30000,
        "sf_ua_browsername": "Chrome",
        "sf_ua_osname": "Mac OS X",
        "entity_type": "RUM Browser Metrics",
        "index_host": env,
    }
    return payload


def apm_base_fields(service_name: str) -> Dict[str, Any]:
    return {
        "computationId": "FskgDsKA4AQ",
        "sf_environment": service_name,
        "sf_organizationID": "FgpBtZ0A0AA",
        "sf_realm": "us1",
        "sf_resolutionMs": 30000,
        "sf_service": service_name,
    }


def iter_apm_streams(service_name: str) -> List[Dict[str, Any]]:
    """Seven JSON metric payloads per run (SLG APM Generator)."""
    streams: List[Dict[str, Any]] = [
        {
            "sf_streamLabel": "non_error_counts",
            "sf_error": "false",
            "metric_name:service.request.count": 50,
        },
        {
            "sf_streamLabel": "error_counts",
            "sf_error": "true",
            "metric_name:service.request.count": 1,
        },
        {
            "sf_streamLabel": "thruput_avg_rate",
            "metric_name:service.request.count": 0.12,
        },
        {
            "sf_streamLabel": "non_error_durations",
            "sf_error": "false",
            "metric_name:service.request.ns.median": 6000000000,
        },
        {
            "sf_streamLabel": "error_durations",
            "sf_error": "true",
            "metric_name:service.request.ns.median": 100000000,
        },
        {
            "sf_streamLabel": "non_error_durations_p99",
            "sf_error": "false",
            "metric_name:service.request.ns.p99": 6000000000,
        },
        {
            "sf_streamLabel": "error_durations_p99",
            "sf_error": "true",
            "metric_name:service.request.ns.p99": 100000000,
        },
    ]
    base = apm_base_fields(service_name)
    payloads: List[Dict[str, Any]] = []
    for stream in streams:
        payload = dict(base)
        payload.update(stream)
        payload["index_host"] = service_name
        payloads.append(payload)
    return payloads


def iter_rum_metric_lines(
    config_name: str,
    settings: Optional[configparser.ConfigParser] = None,
    now: Optional[datetime] = None,
) -> Iterable[str]:
    settings = settings or load_settings(config_name)
    now = now_in_tz(settings, now)

    if not in_demo_window(settings, now):
        return

    env = settings.get("settings", "sf_environment")
    minute = int(now.strftime("%M"))
    payload = apply_rum_metrics(env, minute)
    yield json.dumps(payload, separators=(",", ":"), sort_keys=True)


def iter_apm_metric_lines(
    config_name: str,
    settings: Optional[configparser.ConfigParser] = None,
    now: Optional[datetime] = None,
) -> Iterable[str]:
    settings = settings or load_settings(config_name)
    now = now_in_tz(settings, now)

    if not in_demo_window(settings, now):
        return

    service_name = settings.get("settings", "sf_service")
    for payload in iter_apm_streams(service_name):
        yield json.dumps(payload, separators=(",", ":"), sort_keys=True)
