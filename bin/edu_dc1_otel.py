"""Optional OpenTelemetry instrumentation for edu_dc1_metrics_gen (fail-open)."""

from __future__ import annotations

import configparser

from dc_otel import RunTelemetry as _RunTelemetry


class RunTelemetry(_RunTelemetry):
    def __init__(self, settings: configparser.ConfigParser) -> None:
        super().__init__("edu_dc1", settings)
