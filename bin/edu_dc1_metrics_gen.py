#!/usr/bin/env python3
"""EDU DC1 scripted input — prints metric lines to stdout for splunkd indexing."""

from __future__ import annotations

import sys

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
