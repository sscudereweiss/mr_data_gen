"""Optional OpenTelemetry instrumentation for mr_data_gen scripted inputs (fail-open)."""

from __future__ import annotations

import configparser
import os
import sys
import time
from contextlib import contextmanager
from typing import Any, Iterator, Optional

from datagen_common import RunContext, in_demo_window, resolve_host_name


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

    def __init__(
        self,
        config_name: str,
        settings: configparser.ConfigParser,
        gen_name: Optional[str] = None,
        count_label: str = "events",
        run_context: Optional[RunContext] = None,
    ) -> None:
        self._config_name = config_name
        self._settings = settings
        self._gen_name = gen_name or f"{config_name}_metrics_gen"
        self._count_label = count_label
        self._run_context = run_context
        self._enabled = _get_bool(settings, "observability", "enabled", False)
        self._active = False
        self._start = 0.0
        self._output_count = 0
        self._error: Optional[str] = None
        self._span: Any = None
        self._span_ctx: Any = None
        self._tracer: Any = None
        self._duration_hist: Any = None
        self._output_counter: Any = None
        self._runs_total_counter: Any = None
        self._runs_skipped_counter: Any = None
        self._output_delta_hist: Any = None
        self._errors_counter: Any = None
        self._tracer_provider: Any = None
        self._meter_provider: Any = None

    def set_host_count(self, count: int) -> None:
        """Record stdout line count (hosts, events, or metric documents)."""
        self._output_count = count
        if self._span is not None:
            self._apply_output_attributes()

    def set_error(self, message: str) -> None:
        self._error = message

    def get_trace_id(self) -> Optional[str]:
        if self._span is None:
            return None
        try:
            from opentelemetry.trace import format_trace_id

            ctx = self._span.get_span_context()
            if ctx is None or not ctx.is_valid:
                return None
            return format_trace_id(ctx.trace_id)
        except Exception:  # noqa: BLE001 — fail open
            return None

    @contextmanager
    def child_span(self, name: str) -> Iterator[None]:
        if not self._active or self._tracer is None:
            yield
            return
        with self._tracer.start_as_current_span(f"{self._gen_name}.{name}"):
            yield

    def _apply_output_attributes(self) -> None:
        if self._span is None:
            return
        expected = self._run_context.expected_output_count if self._run_context else 0
        self._span.set_attribute("output_count", self._output_count)
        self._span.set_attribute("expected_output_count", expected)
        self._span.set_attribute("output_delta", self._output_count - expected)
        if self._count_label == "hosts":
            self._span.set_attribute("host_count", self._output_count)

    def __enter__(self) -> RunTelemetry:
        if not self._enabled:
            return self

        try:
            _bootstrap_lib_path()
            self._init_providers()
            self._active = True
            self._start = time.perf_counter()
            span_name = f"{self._gen_name}.run"
            self._tracer = self._tracer_provider.get_tracer(self._gen_name)
            self._span_ctx = self._tracer.start_as_current_span(span_name)
            self._span = self._span_ctx.__enter__()

            ctx = self._run_context
            skip_reason = ctx.skip_reason if ctx else "none"
            self._span.set_attribute("skip_reason", skip_reason)
            self._span.set_attribute("demo_window_active", ctx.demo_window_active if ctx else in_demo_window(self._settings))
            self._span.set_attribute(
                "minute_window_active", ctx.minute_window_active if ctx else True
            )
            self._span.set_attribute("gen_name", self._gen_name)
            self._span.set_attribute("config_name", self._config_name)
            if ctx is not None:
                self._span.set_attribute("run_id", ctx.run_id)
                self._span.set_attribute("minute_of_run", int(ctx.now.strftime("%M")))
                self._span.set_attribute("expected_output_count", ctx.expected_output_count)

            target_index = self._settings.get("settings", "index", fallback="").strip()
            if target_index:
                self._span.set_attribute("target_index", target_index)
            target_sourcetype = self._settings.get("settings", "sourcetype", fallback="").strip()
            if target_sourcetype:
                self._span.set_attribute("target_sourcetype", target_sourcetype)

            interval = self._settings.get("observability", "interval", fallback="").strip()
            if interval:
                self._span.set_attribute("interval", int(interval))
            environment = self._settings.get("observability", "environment", fallback="").strip()
            if environment:
                self._span.set_attribute("deployment.environment", environment)
        except Exception as exc:  # noqa: BLE001 — fail open
            sys.stderr.write(f"{self._gen_name}_otel: disabled ({exc})\n")
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

            self._apply_output_attributes()
            if self._span is not None:
                if self._error:
                    self._span.set_attribute("error", self._error)
                    self._span.set_status(Status(StatusCode.ERROR, self._error))

            if self._duration_hist is not None:
                self._duration_hist.record(duration_ms)
            if self._runs_total_counter is not None:
                self._runs_total_counter.add(1)
            if self._runs_skipped_counter is not None and self._run_context and self._run_context.skip_reason != "none":
                self._runs_skipped_counter.add(1)
            if self._output_counter is not None:
                self._output_counter.add(self._output_count)
            if self._output_delta_hist is not None:
                expected = self._run_context.expected_output_count if self._run_context else 0
                self._output_delta_hist.record(self._output_count - expected)
            if self._errors_counter is not None and self._error:
                self._errors_counter.add(1)

            if self._span_ctx is not None:
                self._span_ctx.__exit__(exc_type, exc_val, exc_tb)

            self._flush()
        except Exception as exc:  # noqa: BLE001 — fail open
            sys.stderr.write(f"{self._gen_name}_otel: export failed ({exc})\n")
        return None

    def _output_count_metric_name(self, metric_prefix: str) -> str:
        if self._settings.has_option("observability", "output_count_metric"):
            suffix = self._settings.get("observability", "output_count_metric").strip()
        elif self._count_label == "hosts":
            suffix = "hosts_emitted"
        else:
            suffix = "events_emitted"
        return f"{metric_prefix}.run.{suffix}"

    def _init_providers(self) -> None:
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        default_service = f"mr_data_gen_{self._config_name}"
        service_name = self._settings.get("observability", "service_name", fallback=default_service)
        endpoint = self._settings.get(
            "observability", "otlp_endpoint", fallback="http://127.0.0.1:4317"
        )
        environment = self._settings.get("observability", "environment", fallback="").strip()
        metric_prefix = self._settings.get(
            "observability", "metric_prefix", fallback=self._config_name
        )

        resource_attrs: dict[str, str] = {
            "service.name": service_name,
            "service.namespace": "mr_data_gen",
            "host.name": resolve_host_name(self._settings),
        }
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

        meter = metrics.get_meter(self._gen_name)
        self._duration_hist = meter.create_histogram(
            f"{metric_prefix}.run.duration_ms",
            unit="ms",
            description="Scripted input run duration",
        )
        self._runs_total_counter = meter.create_counter(
            f"{metric_prefix}.run.runs_total",
            description="Scripted input executions",
        )
        self._runs_skipped_counter = meter.create_counter(
            f"{metric_prefix}.run.runs_skipped",
            description="Runs skipped by demo or minute gate",
        )
        self._output_counter = meter.create_counter(
            self._output_count_metric_name(metric_prefix),
            description="Stdout lines written per scripted-input run",
        )
        self._output_delta_hist = meter.create_histogram(
            f"{metric_prefix}.run.output_delta",
            description="Actual minus expected stdout line count",
        )
        self._errors_counter = meter.create_counter(
            f"{metric_prefix}.run.errors",
            description="Scripted input run failures",
        )

    def _flush(self) -> None:
        if self._tracer_provider is not None:
            self._tracer_provider.force_flush(timeout_millis=5000)
        if self._meter_provider is not None:
            self._meter_provider.force_flush(timeout_millis=5000)
