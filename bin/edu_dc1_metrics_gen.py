#!/usr/bin/env python3
"""EDU DC1 scripted input — prints metric lines to stdout for splunkd indexing."""

from __future__ import annotations

import os
import sys

# Bootstrap vendored OTel deps before any opentelemetry/google imports.
_script_dir = os.path.dirname(os.path.abspath(__file__))
_lib_dir = os.path.join(os.path.dirname(_script_dir), "lib")
if os.path.isdir(_lib_dir) and _lib_dir not in sys.path:
    sys.path.insert(0, _lib_dir)

from edu_dc1_metrics_lib import iter_host_lines, load_settings
from edu_dc1_otel import RunTelemetry


def main() -> int:
    settings = load_settings()
    count = 0
    exit_code = 0
    with RunTelemetry(settings) as tel:
        try:
            for line in iter_host_lines(settings=settings):
                sys.stdout.write(line + "\n")
                count += 1
            sys.stderr.write(f"edu_dc1_metrics_gen: hosts={count}\n")
        except Exception as exc:  # noqa: BLE001 — scripted input must log and exit non-zero
            tel.set_error(str(exc))
            sys.stderr.write(f"edu_dc1_metrics_gen: error={exc}\n")
            exit_code = 1
        finally:
            tel.set_host_count(count)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
