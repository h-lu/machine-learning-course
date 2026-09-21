"""共享运行接口的回归检查。

C01–S06 仍由 ``mlcourse.runtime`` 运行，因此在这里独立核对其数学
性质。S07 以后的新课包使用各课 ``analysis.py``；本文件只检查这个
公共命令行接口和确定性，每课的数值与教学语义由对应的专项测试核对。
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mlcourse.mathops import classification, fit_linear, predict_linear, regression, softmax
from mlcourse.runtime import run_experiment


SHARED_RUNTIME_IDS = ["C01", "C02"] + [f"S{i:02d}" for i in range(1, 7)]
STANDALONE_IDS = [f"S{i:02d}" for i in range(7, 31)]
SPECIALIZED_TESTS = {
    **{f"S{i:02d}": "test_s07_s12_rewrite.py" for i in range(7, 13)},
    **{f"S{i:02d}": "test_pretrained_module.py" for i in range(13, 19)},
    **{f"S{i:02d}": "test_workflow_module.py" for i in range(19, 25)},
    **{f"S{i:02d}": "test_operations_module.py" for i in range(25, 31)},
}


def lesson_dir(lesson: str) -> Path:
    number = int(lesson[1:]) if lesson.startswith("C") else int(lesson[1:]) + 2
    return ROOT / f"lesson-{number:02d}"


def load_shared(lesson: str) -> tuple[dict, dict]:
    directory = lesson_dir(lesson)
    return (
        json.loads((directory / "data/base.json").read_text(encoding="utf-8")),
        json.loads((directory / "config.json").read_text(encoding="utf-8")),
    )


def output_snapshot(directory: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(directory)): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.name != "timings.csv"
    }


class MathematicalChecks(unittest.TestCase):
    def test_linear_fit_recovers_known_relation(self):
        x = np.array(
            [[-2.0, 1.0], [-1.0, 0.0], [0.0, 2.0], [1.0, -1.0], [2.0, 3.0]]
        )
        y = 3 + 2 * x[:, 0] - 0.5 * x[:, 1]
        weights = fit_linear(x, y)
        np.testing.assert_allclose(weights, [3.0, 2.0, -0.5], atol=1e-10)
        np.testing.assert_allclose(predict_linear(x, weights), y, atol=1e-10)

    def test_confusion_counts_and_denominators(self):
        metrics = classification([1, 0, 1, 0], [0.9, 0.8, 0.2, 0.1])
        self.assertEqual(
            [metrics[key] for key in ["tp", "fp", "fn", "tn"]], [1, 1, 1, 1]
        )
        self.assertAlmostEqual(metrics["precision"], 0.5)
        self.assertAlmostEqual(metrics["recall"], 0.5)
        self.assertAlmostEqual(metrics["brier"], (0.01 + 0.64 + 0.64 + 0.01) / 4)
        self.assertIsNone(classification([0, 0], [0.0, 0.0])["recall"])
        self.assertIsNone(classification([1, 0], [0.0, 0.0])["precision"])
        with self.assertRaises(ValueError):
            classification([0], [1.2])

    def test_regression_tail_and_asymmetric_loss(self):
        metrics = regression([2, 0], [0, 1], under_cost=3)
        self.assertAlmostEqual(metrics["mae"], 1.5)
        self.assertAlmostEqual(metrics["rmse"], np.sqrt(2.5))
        self.assertAlmostEqual(metrics["asymmetric_loss"], 3.5)

    def test_softmax_remains_finite_for_large_logits(self):
        np.testing.assert_allclose(softmax([10000, 10000]), [0.5, 0.5])


class SharedRuntimeCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.examples = {lesson: load_shared(lesson) for lesson in SHARED_RUNTIME_IDS}
        cls.results = {
            lesson: run_experiment(lesson, *cls.examples[lesson])
            for lesson in SHARED_RUNTIME_IDS
        }

    def test_each_supported_lesson_produces_real_deterministic_results(self):
        signatures = set()
        for lesson in SHARED_RUNTIME_IDS:
            with self.subTest(lesson=lesson):
                result = self.results[lesson]
                self.assertEqual(result["lesson"], lesson)
                self.assertEqual(result["status"], "example_only")
                self.assertTrue(result["metrics"])
                self.assertTrue(result["stress_test"]["change"])
                self.assertTrue(result["stress_test"]["metrics"])
                self.assertTrue(result["details"])
                self.assertNotIn("scaffold", json.dumps(result))
                self.assertEqual(
                    result, run_experiment(lesson, *self.examples[lesson])
                )
                signatures.add(json.dumps(result["metrics"], sort_keys=True))
        self.assertEqual(len(signatures), len(SHARED_RUNTIME_IDS))

    def test_changed_data_changes_metrics_and_provenance(self):
        for lesson in SHARED_RUNTIME_IDS:
            with self.subTest(lesson=lesson):
                original, config = self.examples[lesson]
                changed = copy.deepcopy(original)
                changed["rows"][0]["wait_minutes"] += 10
                result = run_experiment(lesson, changed, config)
                self.assertNotEqual(result["metrics"], self.results[lesson]["metrics"])
                self.assertNotEqual(
                    result["provenance"]["data_sha256"],
                    self.results[lesson]["provenance"]["data_sha256"],
                )

    def test_cli_accepts_separate_input_and_output_paths(self):
        data, config = load_shared("C02")
        config["rule_slope"] = 3.0
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "data.json").write_text(json.dumps(data), encoding="utf-8")
            (directory / "config.json").write_text(
                json.dumps(config), encoding="utf-8"
            )
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "lesson-02/analysis.py"),
                    "--data",
                    str(directory / "data.json"),
                    "--config",
                    str(directory / "config.json"),
                    "--output",
                    str(directory / "result"),
                ],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            result = json.loads(
                (directory / "result/summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(result["config"]["rule_slope"], 3.0)
            self.assertFalse((directory / "summary.json").exists())


class StandaloneCandidateCoverage(unittest.TestCase):
    def test_every_lesson_has_an_explicit_semantic_test(self):
        self.assertEqual(set(SPECIALIZED_TESTS), set(STANDALONE_IDS))
        for lesson, filename in SPECIALIZED_TESTS.items():
            with self.subTest(lesson=lesson):
                path = ROOT / "tests" / filename
                self.assertTrue(path.is_file())
                source = path.read_text(encoding="utf-8").lower()
                self.assertIn(f"test_{lesson.lower()}_", source)

    def test_support_variant_is_nonempty_and_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for lesson in STANDALONE_IDS:
                with self.subTest(lesson=lesson):
                    directory = lesson_dir(lesson)
                    config = directory / "config-support.json"
                    self.assertTrue(config.is_file())
                    snapshots = []
                    for repetition in (1, 2):
                        output = base / lesson / str(repetition)
                        completed = subprocess.run(
                            [
                                sys.executable,
                                str(directory / "analysis.py"),
                                "--config",
                                str(config),
                                "--output",
                                str(output),
                            ],
                            cwd=ROOT,
                            capture_output=True,
                            text=True,
                            timeout=30,
                            env={**os.environ, "PYTHONHASHSEED": "0"},
                        )
                        self.assertEqual(completed.returncode, 0, completed.stderr)
                        snapshot = output_snapshot(output)
                        self.assertIn("summary.json", snapshot)
                        self.assertGreaterEqual(len(snapshot), 2)
                        timing = output / "timings.csv"
                        if timing.exists():
                            self.assertGreater(timing.stat().st_size, 0)
                        summary = json.loads(snapshot["summary.json"])
                        self.assertIsInstance(summary, dict)
                        self.assertTrue(summary)
                        snapshots.append(snapshot)
                    self.assertEqual(snapshots[0], snapshots[1])


if __name__ == "__main__":
    unittest.main()
