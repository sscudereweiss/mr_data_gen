#!/usr/bin/env python3
"""Shared scripted-input runner for mr_data_gen datacenter metrics."""

from __future__ import annotations

import os
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
_lib_dir = os.path.join(os.path.dirname(_script_dir), "lib")
if os.path.isdir(_lib_dir) and _lib_dir not in sys.path:
    sys.path.insert(0, _lib_dir)

from dc_metrics_lib import iter_host_lines, load_settings
from dc_otel import RunTelemetry


def run(config_name: str) -> int:
    settings = load_settings(config_name)
    count = 0
    exit_code = 0
    with RunTelemetry(config_name, settings) as tel:
        try:
            for line in iter_host_lines(config_name, settings=settings):
                sys.stdout.write(line + "\n")
                count += 1
            sys.stderr.write(f"{config_name}_metrics_gen: hosts={count}\n")
        except Exception as exc:  # noqa: BLE001 — scripted input must log and exit non-zero
            tel.set_error(str(exc))
            sys.stderr.write(f"{config_name}_metrics_gen: error={exc}\n")
            exit_code = 1
        finally:
            tel.set_host_count(count)
    return exit_code


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("usage: dc_metrics_gen.py <config_name>\n")
        sys.exit(2)
    sys.exit(run(sys.argv[1]))
