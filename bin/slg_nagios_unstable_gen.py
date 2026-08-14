#!/usr/bin/env python3
"""SLG Nagios unstable alert scripted input."""

from __future__ import annotations

import os
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from datagen_runner import run
from raw_event_lib import iter_raw_event_lines

CONFIG_NAME = "slg_nagios_unstable"


def main() -> int:
    return run(CONFIG_NAME, iter_raw_event_lines, gen_name="slg_nagios_unstable_gen")


if __name__ == "__main__":
    sys.exit(main())
