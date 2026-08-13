"""Optional OpenTelemetry instrumentation for edu_dc1_metrics_gen (fail-open)."""

from __future__ import annotations

import configparser
import os
import sys
import time
from typing import Any, Optional

from edu_dc1_metrics_lib import in_demo_window


def _bootstrap_lib_path() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lib_dir = os.path.join(os.path.dirname(script_dir), "lib")
    if os.path.isdir(lib_dir) and lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)


def _get_bool(parser: configparser.ConfigParser, section: str, option: str, default: bool) -> bool:
    if not parser.has_option(section, option):
        return default
    return parser.get(section, option).strip().lower() in ("1", "true", "yes", "on")


class RunTelemetry:
    """Context manager: one trace span and custom metrics per scripted-input run."""

    def __init__(self, settings: configparser.ConfigParser) -> None:
        self._settings = settings
        self._enabled = _get_bool(settings, "observability", "enabled", False)
        self._active = False
        self._start = 0.0
        self._host_count = 0
        self._error: Optional[str] = None
        self._span: Any = None
        self._span_ctx: Any = None
        self._meter: Any = None
        self._duration_hist: Any = None
        self._hosts_counter: Any = None
        self._errors_counter: Any = None
        self._tracer_provider: Any = None
        self._meter_provider: Any = None

    def set_host_count(self, count: int) -> None:
        self._host_count = count

    def set_error(self, message: str) -> None:
        self._error = message

    def __enter__(self) -> RunTelemetry:
        if not self._enabled:
            return self

        try:
            _bootstrap_lib_path()
            self._init_providers()
            self._active = True
            self._start = time.perf_counter()
            tracer = self._tracer_provider.get_tracer("edu_dc1_metrics_gen")
            self._span_ctx = tracer.start_as_current_span("edu_dc1_metrics_gen.run")
            self._span = self._span_ctx.__enter__()
            self._span.set_attribute("demo_window_active", in_demo_window(self._settings))
            interval = self._settings.get("observability", "interval", fallback="").strip()
            if interval:
                self._span.set_attribute("interval", int(interval))
            environment = self._settings.get("observability", "environment", fallback="").strip()
            if environment:
                self._span.set_attribute("deployment.environment", environment)
        except Exception as exc:  # noqa: BLE001 — fail open
            sys.stderr.write(f"edu_dc1_otel: disabled ({exc})\n")
            self._active = False
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if not self._active:
            return None

        duration_ms = (time.perf_counter() - self._start) * 1000.0
        if exc_val is not None and self._error is None:
            self._error = str(exc_val)

        try:
            from opentelemetry.trace import Status, StatusCode

            if self._span is not None:
                self._span.set_attribute("host_count", self._host_count)
                if self._error:
                    self._span.set_attribute("error", self._error)
                    self._span.set_status(Status(StatusCode.ERROR, self._error))

            if self._duration_hist is not None:
                self._duration_hist.record(duration_ms)
            if self._hosts_counter is not None:
                self._hosts_counter.add(self._host_count)
            if self._errors_counter is not None and self._error:
                self._errors_counter.add(1)

            if self._span_ctx is not None:
                self._span_ctx.__exit__(exc_type, exc_val, exc_tb)

            self._flush()
        except Exception as exc:  # noqa: BLE001 — fail open
            sys.stderr.write(f"edu_dc1_otel: export failed ({exc})\n")
        return None

    def _init_providers(self) -> None:
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        service_name = self._settings.get(
            "observability", "service_name", fallback="mr_data_gen_edu_dc1"
        )
        endpoint = self._settings.get(
            "observability", "otlp_endpoint", fallback="http://127.0.0.1:4317"
        )
        environment = self._settings.get("observability", "environment", fallback="").strip()

        resource_attrs: dict[str, str] = {"service.name": service_name}
        if environment:
            resource_attrs["deployment.environment"] = environment

        resource = Resource.create(resource_attrs)

        span_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        self._tracer_provider = TracerProvider(resource=resource)
        self._tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))

        metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
        metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
        self._meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])

        from opentelemetry import metrics, trace

        trace.set_tracer_provider(self._tracer_provider)
        metrics.set_meter_provider(self._meter_provider)

        meter = metrics.get_meter("edu_dc1_metrics_gen")
        self._duration_hist = meter.create_histogram(
            "edu_dc1.run.duration_ms",
            unit="ms",
            description="Scripted input run duration",
        )
        self._hosts_counter = meter.create_counter(
            "edu_dc1.run.hosts_emitted",
            description="Hosts written to stdout per run",
        )
        self._errors_counter = meter.create_counter(
            "edu_dc1.run.errors",
            description="Scripted input run failures",
        )

    def _flush(self) -> None:
        if self._tracer_provider is not None:
            self._tracer_provider.force_flush(timeout_millis=5000)
        if self._meter_provider is not None:
            self._meter_provider.force_flush(timeout_millis=5000)
