# Model card

**Type:** fitted per-feature median/robust-scale anomaly model plus reference-binned distribution monitoring. Training occurs in memory for every comparison. There are no learned neural weights or external model services.

**Intended use:** small, numeric ML-input monitoring experiments and human-reviewed batch checks. Reference data should represent the intended operating context and have consistent units. Thresholds must be tuned against labeled operational examples and false-alert costs.

**Data:** original synthetic latency and payload values, seeded with Python Random(20261027). No real service measurements. Reference uses 200 observations near 100 ms / 50 KB; current uses 100 observations near 180 ms / 50 KB. Shared generator assumptions make this an easy test. It is not a benchmark.

**Evaluation:** tests cover stable self-comparison, a deliberately large shift, constant features, zero-MAD nonconstant features, and numerical/input failure cases. No claims of production accuracy, fairness, calibration, causality, attack detection, or measured cost savings are made.

**Limitations:** independent features miss correlation shifts; distributions are reduced to coarse bins; unequal samples and smoothing affect scores; zero-scale fallback is conservative within the reference range; no missing/categorical/time-series support; no adaptation, seasonality, labels, or concept-drift estimator. Small samples are permitted for demos but may yield unstable statistics. Distribution shift alone cannot establish degraded model performance.

**Human control:** flags always require review. Compare labels/outcomes and operational context; inspect units and schema changes; choose whether to retrain or update reference data. Avoid automated high-stakes decisions.
