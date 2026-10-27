# Security and trust boundaries

Inputs are untrusted JSON, never instructions or executable serialized objects. Parsing rejects duplicate keys and non-finite constants. Files are read with an 8 MiB bound; schemas have row/feature limits. No shell commands, subprocesses, networking, database, dynamic imports, eval, pickle, or outbound telemetry exist in runtime code. The CLI reads explicitly selected files and writes JSON to stdout; it does not mutate inputs.

A caller can still choose a blocking special file such as a FIFO; only use regular local files from trusted workflows. Input parsing and report construction consume CPU/memory within the documented data limits. The in-process Python API accepts already-loaded data and does not enforce the CLI byte limit.

Reports expose medians, scale, bin edges, feature names, and row indices. Treat them as potentially sensitive and control redirected output yourself. Errors omit input content and filenames. No authentication is needed because there is no listening service. If wrapping in a service, add authentication, quotas, timeouts, and file isolation.

Security review covered bounded parsing, schema confusion, numerical behavior, output leakage, dependency surface, and model-loading risks. Statistical manipulation and poisoned reference data remain possible: human review and independent labeled outcome checks are required. Never automatically block people or systems based only on these flags.

Report non-sensitive reproducible bugs via Issues; use private vulnerability reporting if enabled for sensitive details. Never attach real customer data or credentials.
