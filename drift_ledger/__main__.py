"""Bounded JSON CLI. Exit 0: no flags; 1: flags; 2: invalid input/I/O."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .core import compare

MAX_BYTES = 8 * 1024 * 1024


def reject_constant(value: str) -> None:
    raise ValueError("JSON non-finite constants are forbidden")


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON keys are forbidden")
        result[key] = value
    return result


def read_json(path: Path) -> Any:
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Input exceeds 8 MiB")
    return json.loads(data, parse_constant=reject_constant, object_pairs_hook=unique_object)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fit a robust numeric baseline and inspect a new ML input batch locally."
    )
    parser.add_argument("reference", type=Path)
    parser.add_argument("current", type=Path)
    parser.add_argument("--z-threshold", type=float, default=3.5)
    parser.add_argument("--drift-threshold", type=float, default=0.1)
    args = parser.parse_args()
    try:
        report = compare(
            read_json(args.reference),
            read_json(args.current),
            args.z_threshold,
            args.drift_threshold,
        )
        print(json.dumps(report, indent=2, allow_nan=False))
        return int(
            report["anomalous_row_count"] > 0 or any(f["drift_flag"] for f in report["features"])
        )
    except (OSError, ValueError, OverflowError, RecursionError) as error:
        # Do not echo input values, file contents, or potentially sensitive filenames.
        print(
            json.dumps({"error": "Invalid input or unreadable file", "type": type(error).__name__}),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
