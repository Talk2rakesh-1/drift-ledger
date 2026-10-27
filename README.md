# DriftLedger

[![CI](https://github.com/Talk2rakesh-1/drift-ledger/actions/workflows/ci.yml/badge.svg)](https://github.com/Talk2rakesh-1/drift-ledger/actions/workflows/ci.yml)

A local AI-operations CLI that fits robust, per-feature anomaly baselines from reference observations and monitors a new numeric batch. Reports include feature-level distribution shifts, anomalous row indices, learned statistics, and explicit human-review requirements. No cloud, model download, API key, or runtime dependency.

**Functional portfolio MVP, not a validated production detector.** It is a statistical anomaly model and ML-input monitoring tool, not a generative AI system. A distribution shift does not prove accuracy loss, an attack, or concept drift.

## Try it

Python 3.10+; run directly from the checkout:

```sh
python -m drift_ledger examples/reference.json examples/reference.json
python -m drift_ledger examples/reference.json examples/shifted.json
```

Or install with `pip install .` and use `drift-ledger`. Input files are arrays of numeric objects, e.g. `[{"latency_ms": 102, "payload_kb": 49}, ...]`, with **20–10,000 rows**, **1–32 matching features**, and an **8 MiB file limit**. Values must be finite and within ±1e12. Missing values, booleans, duplicate JSON keys, and schema changes are rejected. Feature names allow ASCII letters, digits, and underscores only.

Exit codes: **0** no flags, **1** anomaly or drift flagged, **2** invalid input/I/O. JSON reports go to stdout; errors go to stderr without raw values or filenames. Redirect reports to files when useful. Reports contain aggregate feature statistics and row indices, which can still be sensitive.

## Model and monitoring

1. Fit each feature's median and MAD using only reference data. Use `1.4826 × MAD` as a robust scale.
2. If MAD is zero, use IQR/1.349. If that is also zero, flag only values outside the reference range; the report identifies the fallback.
3. Flag observations whose absolute scaled deviation exceeds `--z-threshold` (default 3.5).
4. Learn fixed quantile bins from the reference, including explicit underflow/overflow boundaries. Smooth counts by 0.5 and compare reference/current distributions using base-2 Jensen–Shannon **divergence**, not its square-root distance.
5. Flag divergence at or above `--drift-threshold` (default 0.1).

Thresholds are heuristics, not calibrated confidence or statistical-significance tests. Correlated changes can escape independent feature checks. Seasonal, multimodal, discrete, or very small samples can produce misleading results. Refit intentionally after review, not automatically on potentially contaminated data. No pickle or executable model file is loaded.

## Reproducible example

`examples/` contains original seeded synthetic service measurements: 200 reference rows and 100 rows with an intentionally large latency shift. The payload distribution is approximately stable. This checks implementation behavior, not real-world sensitivity, specificity, or business value. See [model card](docs/MODEL_CARD.md) and [verification](docs/VERIFICATION.md).

## Development

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
ruff check .
ruff format --check .
mypy drift_ledger
coverage run --source=drift_ledger -m unittest discover -s tests -v
coverage report
bandit -r drift_ledger -ll
pip-audit -r requirements-dev.txt
pip-audit -r requirements.txt
```

Twelve tests include CLI integration, input limits, deterministic invariance, constant/zero-MAD baselines, distribution properties, and synthetic regression. CI tests Python 3.10 and 3.13, installed-package smoke behavior, dependency advisories, and full-history secrets. No web server or UI is implemented; UI checks are not applicable.

[Research](docs/RESEARCH.md) · [Security](SECURITY.md) · [Licensing](THIRD_PARTY.md). MIT licensed.
