# Verification — 2026-10-27

- All 12 unit/integration tests passed locally (Python 3.12.14, also checked on 3.9.6); supported CI targets are Python 3.10 and 3.13.
- Coverage: 88% total statement coverage, 100% core module coverage. CLI subprocess execution is tested but not included in parent-process coverage.
- Ruff lint/format, strict mypy, and Bandit: passed.
- CLI smoke: unchanged batch returns 0; shifted fixture returns 1 and JSON findings; invalid input returns 2.
- pip-audit: no known vulnerabilities in runtime or resolved development requirements on Python 3.12.14. The initial Python 3.9 environment selected outdated transitive tools; supported Python versions resolve patched packages. Full-history Gitleaks runs before publication and in CI.
- Manual security/license review completed; zero runtime dependencies, original fixtures, no external model weights or datasets.
- UI/browser/container tests: not applicable; the deliverable is a local CLI, not a service or graphical application.

The synthetic fixtures deliberately encode a large shift. Success here does not establish real-world detection accuracy, calibration, or false-positive rates. No operational data, device integration, throughput benchmark, or high-stakes deployment validation was performed.
