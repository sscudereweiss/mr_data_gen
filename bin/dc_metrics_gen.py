#!/usr/bin/env python3
"""Shared scripted-input runner for mr_data_gen datacenter metrics."""

from __future__ import annotations

import os
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from datagen_runner import run as runner_run
from dc_metrics_lib import iter_host_lines


def run(config_name: str) -> int:
    return runner_run(
        config_name,
        iter_host_lines,
        gen_name=f"{config_name}_metrics_gen",
        count_label="hosts",
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("usage: dc_metrics_gen.py <config_name>\n")
        sys.exit(2)
    sys.exit(run(sys.argv[1]))
