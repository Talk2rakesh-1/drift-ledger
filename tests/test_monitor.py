import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from drift_ledger.__main__ import MAX_BYTES, read_json
from drift_ledger.core import compare, histogram, js_divergence, validate_rows


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.reference = [{"x": float(i), "y": float(i % 5)} for i in range(100)]

    def test_identical_no_drift(self):
        report = compare(self.reference, self.reference)
        self.assertEqual(report["anomalous_row_count"], 0)
        self.assertTrue(all(f["js_divergence_bits"] == 0 for f in report["features"]))

    def test_shift_detected_and_attributed(self):
        current = [{"x": row["x"] + 1000, "y": row["y"]} for row in self.reference]
        report = compare(self.reference, current)
        self.assertEqual(report["anomalous_row_count"], 100)
        self.assertTrue(report["features"][0]["drift_flag"])
        self.assertFalse(report["features"][1]["drift_flag"])
        self.assertEqual(report["anomalous_rows"][0]["features"], ["x"])

    def test_constant_reference(self):
        reference = [{"x": 5}] * 20
        self.assertEqual(compare(reference, reference)["anomalous_row_count"], 0)
        report = compare(reference, [{"x": 6}] * 20)
        self.assertEqual(report["anomalous_row_count"], 20)
        self.assertTrue(report["features"][0]["drift_flag"])
        self.assertEqual(report["features"][0]["scale_method"], "reference_range_only")

    def test_zero_mad_not_constant(self):
        reference = [{"x": 0}] * 18 + [{"x": 10}] * 2
        self.assertEqual(compare(reference, reference)["anomalous_row_count"], 0)
        self.assertEqual(compare(reference, [{"x": 11}] * 20)["anomalous_row_count"], 20)

    def test_iqr_fallback(self):
        reference = [{"x": 0}] * 12 + [{"x": 10}] * 8
        self.assertEqual(
            compare(reference, reference)["features"][0]["scale_method"], "interquartile_range"
        )

    def test_schema_and_bounds(self):
        for bad in [
            [],
            [{}] * 20,
            [{"x": True}] * 20,
            [{"x": math.nan}] * 20,
            [{"x": math.inf}] * 20,
            [{"x": 1e13}] * 20,
            [{"x": "1"}] * 20,
            [{"bad key": 1}] * 20,
            [{"x": 1}] * 19 + [{"y": 2}],
            [{str(i): 0 for i in range(33)}] * 20,
            [{"x": 1}] * 10001,
        ]:
            with self.subTest(bad=str(bad)[:50]), self.assertRaises(ValueError):
                validate_rows(bad)
        with self.assertRaises(ValueError):
            compare(self.reference, [{"z": 1}] * 20)

    def test_threshold_validation(self):
        for z in [0, 21, math.nan, math.inf]:
            with self.assertRaises(ValueError):
                compare(self.reference, self.reference, z_threshold=z)
        for d in [0, -1, 2, math.nan]:
            with self.assertRaises(ValueError):
                compare(self.reference, self.reference, drift_threshold=d)

    def test_divergence_properties(self):
        a, b = histogram([1, 2, 3], [1, 2]), histogram([10, 10], [1, 2])
        self.assertAlmostEqual(sum(a), 1)
        self.assertAlmostEqual(js_divergence(a, b), js_divergence(b, a))
        self.assertTrue(0 <= js_divergence(a, b) <= 1)

    def test_permutation_invariance(self):
        a, b = (
            compare(self.reference, self.reference),
            compare(list(reversed(self.reference)), self.reference),
        )
        self.assertEqual(a, b)

    def test_json_reader_rejects_ambiguous_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for content in [
                '{"x":1,"x":2}',
                "[NaN]",
                "[Infinity]",
                "broken",
                "x" * (MAX_BYTES + 1),
            ]:
                path.write_text(content)
                with self.assertRaises(ValueError):
                    read_json(path)

    def test_cli_exit_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "reference.json"
            current = Path(directory) / "current.json"
            reference.write_text(json.dumps(self.reference))
            for rows, code in [(self.reference, 0), ([{"x": 10000, "y": 1}] * 20, 1), ([], 2)]:
                current.write_text(json.dumps(rows))
                result = subprocess.run(
                    [sys.executable, "-m", "drift_ledger", str(reference), str(current)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertIsInstance(
                    json.loads(result.stderr if code == 2 else result.stdout), dict
                )

    def test_synthetic_regression(self):
        report = compare(
            read_json(Path("examples/reference.json")), read_json(Path("examples/shifted.json"))
        )
        self.assertTrue(report["features"][0]["drift_flag"])
        self.assertFalse(report["features"][1]["drift_flag"])
        self.assertGreater(report["anomalous_row_count"], 90)


if __name__ == "__main__":
    unittest.main()
