#!/usr/bin/env python3
"""SLG RUM metrics scripted input."""

from __future__ import annotations

import os
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from datagen_runner import run
from sim_metrics_lib import iter_rum_metric_lines

CONFIG_NAME = "slg_rum"


def main() -> int:
    return run(CONFIG_NAME, iter_rum_metric_lines, gen_name="slg_rum_metrics_gen")


if __name__ == "__main__":
    sys.exit(main())
