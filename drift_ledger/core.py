"""Inspectable robust baseline model; no executable model serialization."""

from __future__ import annotations

import math
import statistics
from bisect import bisect_right
from collections import Counter
from typing import Any

MAX_ROWS = 10000
MAX_FEATURES = 32
BINS = 10


def validate_rows(value: Any) -> list[dict[str, float]]:
    if not isinstance(value, list) or not 20 <= len(value) <= MAX_ROWS:
        raise ValueError("Expected 20–10000 numeric observation objects")
    first = value[0]
    if not isinstance(first, dict) or not 1 <= len(first) <= MAX_FEATURES:
        raise ValueError("Expected 1–32 named features")
    keys = set(first)
    if any(
        not isinstance(k, str)
        or not 1 <= len(k) <= 64
        or not k.isascii()
        or not all(c.isalnum() or c == "_" for c in k)
        for k in keys
    ):
        raise ValueError("Feature names must be 1–64 ASCII letters, digits, or underscores")
    rows = []
    for row in value:
        if not isinstance(row, dict) or set(row) != keys:
            raise ValueError(
                "All rows must have exactly the same features; missing data is rejected"
            )
        clean = {}
        for key, number in row.items():
            if isinstance(number, bool) or not isinstance(number, (int, float)):
                raise ValueError("Feature values must be finite numbers, not booleans")
            if not math.isfinite(number) or abs(number) > 1e12:
                raise ValueError("Feature values must be finite and within ±1e12")
            clean[key] = float(number)
        rows.append(clean)
    return rows


def quantile(sorted_values: list[float], fraction: float) -> float:
    position = (len(sorted_values) - 1) * fraction
    low = math.floor(position)
    high = math.ceil(position)
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (position - low)


def histogram(values: list[float], edges: list[float]) -> list[float]:
    counts = Counter(bisect_right(edges, number) for number in values)
    # Fixed bins learned only from reference; additive smoothing handles empty bins.
    return [
        (counts[i] + 0.5) / (len(values) + 0.5 * (len(edges) + 1)) for i in range(len(edges) + 1)
    ]


def js_divergence(left: list[float], right: list[float]) -> float:
    middle = [(a + b) / 2 for a, b in zip(left, right)]
    return sum(
        0.5 * (a * math.log2(a / m) + b * math.log2(b / m)) for a, b, m in zip(left, right, middle)
    )


def compare(
    reference: Any, current: Any, z_threshold: float = 3.5, drift_threshold: float = 0.1
) -> dict[str, Any]:
    if not math.isfinite(z_threshold) or not 1 <= z_threshold <= 20:
        raise ValueError("z threshold must be finite and between 1 and 20")
    if not math.isfinite(drift_threshold) or not 0 < drift_threshold <= 1:
        raise ValueError("drift threshold must be finite and in (0, 1]")
    baseline = validate_rows(reference)
    batch = validate_rows(current)
    if set(baseline[0]) != set(batch[0]):
        raise ValueError("Current features must exactly match the reference schema")
    features = []
    row_findings: dict[int, list[str]] = {}
    for name in sorted(baseline[0]):
        before = sorted(row[name] for row in baseline)
        after = [row[name] for row in batch]
        median = statistics.median(before)
        mad = statistics.median(abs(v - median) for v in before)
        # Zero MAD is not equivalent to a constant feature. Avoid a fabricated tiny scale.
        scale = 1.4826 * mad
        scale_method = "median_absolute_deviation"
        if scale == 0:
            scale = (quantile(before, 0.75) - quantile(before, 0.25)) / 1.349
            scale_method = "interquartile_range"
        if scale == 0:
            scale_method = "reference_range_only"
        anomaly_count = 0
        for index, value in enumerate(after):
            anomalous = (
                abs(value - median) / scale > z_threshold
                if scale > 0
                else value < before[0] or value > before[-1]
            )
            if anomalous:
                anomaly_count += 1
                row_findings.setdefault(index, []).append(name)
        # Include reference extrema so a constant reference still exposes out-of-range shifts.
        edges = sorted(
            set(
                [before[0], math.nextafter(before[-1], math.inf)]
                + [quantile(before, i / BINS) for i in range(1, BINS)]
            )
        )
        divergence = js_divergence(histogram(before, edges), histogram(after, edges))
        features.append(
            {
                "name": name,
                "reference_median": median,
                "reference_mad": mad,
                "scale_method": scale_method,
                "scale": scale,
                "bin_edges": edges,
                "js_divergence_bits": divergence,
                "drift_flag": divergence >= drift_threshold,
                "anomaly_count": anomaly_count,
                "anomaly_rate": anomaly_count / len(batch),
            }
        )
    return {
        "schema_version": 1,
        "reference_count": len(baseline),
        "current_count": len(batch),
        "z_threshold": z_threshold,
        "drift_threshold": drift_threshold,
        "features": features,
        "anomalous_rows": [
            {"row_index": i, "features": f} for i, f in sorted(row_findings.items())
        ],
        "anomalous_row_count": len(row_findings),
        "review_required": True,
        "warning": "Heuristic distribution and anomaly signals; not probabilities, accuracy measurements, or evidence of an attack.",
    }
