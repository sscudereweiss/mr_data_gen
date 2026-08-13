#!/usr/bin/env python3
"""EDU DC2 scripted input — prints metric lines to stdout for splunkd indexing."""

from __future__ import annotations

import os
import sys

_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from dc_metrics_gen import run

CONFIG_NAME = "edu_dc2"


def main() -> int:
    return run(CONFIG_NAME)


if __name__ == "__main__":
    sys.exit(main())
