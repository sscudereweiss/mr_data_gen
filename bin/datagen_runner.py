#!/usr/bin/env python3
"""Shared scripted-input runner for mr_data_gen generators."""

from __future__ import annotations

import os
import sys
import uuid
from typing import Callable, Iterable, Optional

_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from datagen_common import (
    build_run_context,
    load_settings,
    log_correlation_enabled,
    resolve_service_name,
)
from dc_otel import RunTelemetry

LineIterator = Callable[..., Iterable[str]]


def _write_stderr_summary(
    gen_name: str,
    count_label: str,
    count: int,
    run_id: str,
    trace_id: Optional[str],
    skip_reason: str,
    expected: int,
    service_name: str,
) -> None:
    trace_token = trace_id if trace_id else "-"
    sys.stderr.write(
        f"{gen_name}: {count_label}={count} run_id={run_id} trace_id={trace_token} "
        f"skip_reason={skip_reason} expected={expected} service={service_name}\n"
    )


def run(
    config_name: str,
    iter_fn: LineIterator,
    gen_name: Optional[str] = None,
    count_label: str = "events",
) -> int:
    settings = load_settings(config_name)
    gen_name = gen_name or f"{config_name}_gen"
    run_id = str(uuid.uuid4())
    ctx = build_run_context(settings, config_name, run_id)
    service_name = resolve_service_name(settings, config_name)
    count = 0
    exit_code = 0

    with RunTelemetry(
        config_name,
        settings,
        gen_name=gen_name,
        count_label=count_label,
        run_context=ctx,
    ) as tel:
        try:
            with tel.child_span("prepare"):
                skip_reason = ctx.skip_reason
                expected = ctx.expected_output_count

            with tel.child_span("generate"):
                if skip_reason == "none":
                    for line in iter_fn(config_name, settings=settings):
                        sys.stdout.write(line + "\n")
                        count += 1

            with tel.child_span("finalize"):
                tel.set_host_count(count)
                trace_id = tel.get_trace_id()
                if log_correlation_enabled(settings):
                    _write_stderr_summary(
                        gen_name,
                        count_label,
                        count,
                        run_id,
                        trace_id,
                        skip_reason,
                        expected,
                        service_name,
                    )
        except Exception as exc:  # noqa: BLE001 — scripted input must log and exit non-zero
            tel.set_error(str(exc))
            tel.set_host_count(count)
            trace_id = tel.get_trace_id()
            sys.stderr.write(f"{gen_name}: error={exc}\n")
            if log_correlation_enabled(settings):
                _write_stderr_summary(
                    gen_name,
                    count_label,
                    count,
                    run_id,
                    trace_id,
                    ctx.skip_reason,
                    ctx.expected_output_count,
                    service_name,
                )
            exit_code = 1

    return exit_code
