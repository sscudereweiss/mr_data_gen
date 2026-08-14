#!/usr/bin/env python3
"""Shared scripted-input runner for mr_data_gen generators."""

from __future__ import annotations

import os
import sys
from typing import Callable, Iterable, Optional

_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from datagen_common import load_settings
from dc_otel import RunTelemetry

LineIterator = Callable[..., Iterable[str]]


def run(
    config_name: str,
    iter_fn: LineIterator,
    gen_name: Optional[str] = None,
    count_label: str = "events",
) -> int:
    settings = load_settings(config_name)
    gen_name = gen_name or f"{config_name}_gen"
    count = 0
    exit_code = 0
    with RunTelemetry(config_name, settings) as tel:
        try:
            for line in iter_fn(config_name, settings=settings):
                sys.stdout.write(line + "\n")
                count += 1
            sys.stderr.write(f"{gen_name}: {count_label}={count}\n")
        except Exception as exc:  # noqa: BLE001 — scripted input must log and exit non-zero
            tel.set_error(str(exc))
            sys.stderr.write(f"{gen_name}: error={exc}\n")
            exit_code = 1
        finally:
            tel.set_host_count(count)
    return exit_code


if __name__ == "__main__":
    sys.stderr.write("usage: import datagen_runner from a generator script\n")
    sys.exit(2)
