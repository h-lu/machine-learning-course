"""检查起步工具的计算；不把教师偏好的模型或结论作为学生答案。"""

from __future__ import annotations
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.runtime import run_experiment
from mlcourse.mathops import (
    classification,
    regression,
    fit_linear,
    predict_linear,
    softmax,
    kmeans,
)
from mlcourse.experiments import (
    attention,
    transformer,
    sampling_distribution,
    transition,
    value_iteration,
)

IDS = ["C01", "C02"] + [f"S{i:02d}" for i in range(1, 31)]


def lesson_dir(lesson):
    number = int(lesson[1:]) if lesson.startswith("C") else int(lesson[1:]) + 2
    return ROOT / f"lesson-{number:02d}"

def load(lesson):
    p = lesson_dir(lesson)
    return json.loads((p / "data/base.json").read_text()), json.loads(
        (p / "config.json").read_text()
    )


class MathematicalChecks(unittest.TestCase):
    def test_linear_fit_recovers_known_relation(self):
        x = np.array([[-2.0, 1.0], [-1.0, 0.0], [0.0, 2.0], [1.0, -1.0], [2.0, 3.0]])
        y = 3 + 2 * x[:, 0] - 0.5 * x[:, 1]
        w = fit_linear(x, y)
        np.testing.assert_allclose(w, [3.0, 2.0, -0.5], atol=1e-10)
        np.testing.assert_allclose(predict_linear(x, w), y, atol=1e-10)

    def test_confusion_counts_and_denominators(self):
        m = classification([1, 0, 1, 0], [0.9, 0.8, 0.2, 0.1])
        self.assertEqual([m[k] for k in ["tp", "fp", "fn", "tn"]], [1, 1, 1, 1])
        self.assertAlmostEqual(m["precision"], 0.5)
        self.assertAlmostEqual(m["recall"], 0.5)
        self.assertAlmostEqual(m["brier"], (0.01 + 0.64 + 0.64 + 0.01) / 4)
        self.assertIsNone(classification([0, 0], [0.0, 0.0])["recall"])
        self.assertIsNone(classification([1, 0], [0.0, 0.0])["precision"])
        with self.assertRaises(ValueError):
            classification([0], [1.2])

    def test_regression_tail_and_asymmetric_loss(self):
        m = regression([2, 0], [0, 1], under_cost=3)
        self.assertAlmostEqual(m["mae"], 1.5)
        self.assertAlmostEqual(m["rmse"], np.sqrt(2.5))
        self.assertAlmostEqual(m["asymmetric_loss"], 3.5)

    def test_attention_mask_blocks_future_inputs(self):
        vectors = np.array([[1.0, 0.0], [0.0, 1.0], [0.5, 0.2]])
        w, y = attention(vectors, True)
        self.assertEqual(float(np.triu(w, 1).sum()), 0.0)
        np.testing.assert_allclose(w.sum(axis=1), 1)
        changed = vectors.copy()
        changed[-1] += [3, 5]
        np.testing.assert_allclose(attention(changed, True)[1][0], y[0])
        self.assertFalse(
            np.allclose(
                attention(changed, False)[1][0], attention(vectors, False)[1][0]
            )
        )

    def test_transformer_residual_path_still_respects_causality(self):
        d, _ = load("S18")
        x = np.array(d["vectors"])
        h, _ = transformer(x, True, 7)
        changed = x.copy()
        changed[-1] += [2, -1, 3, -2]
        h2, _ = transformer(changed, True, 7)
        np.testing.assert_allclose(h[0], h2[0], atol=1e-12)
        self.assertFalse(np.allclose(h[-1], h2[-1]))

    def test_sampling_normalizes_after_filtering(self):
        p = sampling_distribution(np.array([5.0, 2.0, 1.0, 0.0]), 0.8, 2, 0.9)
        self.assertAlmostEqual(float(p.sum()), 1.0)
        self.assertLessEqual(int((p > 0).sum()), 2)
        self.assertGreater(p[0], p[1])
        with self.assertRaises(ValueError):
            sampling_distribution(np.array([0.0, 1.0]), 0.0, 1, 0.9)
        np.testing.assert_allclose(softmax([10000, 10000]), [0.5, 0.5])

    def test_terminal_reward_has_no_future_bootstrap(self):
        d, _ = load("S27")
        nxt, reward, done = transition(d, 14, 1)
        self.assertEqual((nxt, reward, done), (15, 1.0, True))
        self.assertEqual(transition(d, 15, 0), (15, 0.0, True))
        self.assertEqual(transition(d, 0, 0), (0, -0.04, False))
        values, policy, residual, _ = value_iteration(d, 0.9)
        expected = sum(0.9**t * -0.04 for t in range(5)) + 0.9**5
        self.assertAlmostEqual(values[0], expected, places=9)
        self.assertLess(residual, 1e-8)

    def test_kmeans_assignments_use_final_centres(self):
        x = np.array([[0.0, 0.0], [0.0, 1.0], [4.0, 4.0], [4.0, 5.0], [8.0, 0.0]])
        labels, centres, inertia = kmeans(x, k=2, steps=1, seed=4)
        nearest = np.argmin(((x[:, None] - centres[None]) ** 2).sum(axis=2), axis=1)
        np.testing.assert_array_equal(labels, nearest)
        self.assertAlmostEqual(inertia, float(((x - centres[labels]) ** 2).sum()))

    def test_value_iteration_reports_failure_to_converge(self):
        d, _ = load("S27")
        d["step_reward"] = 0.2
        with self.assertRaisesRegex(ValueError, "仍未收敛"):
            value_iteration(d, 0.999999, tolerance=1e-8)


class CompleteLessonCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.examples = {lesson: load(lesson) for lesson in IDS}
        cls.results = {
            lesson: run_experiment(lesson, *cls.examples[lesson]) for lesson in IDS
        }

    def test_every_lesson_produces_numerical_results_and_real_stress(self):
        signatures = set()
        for lesson in IDS:
            with self.subTest(lesson=lesson):
                r = self.results[lesson]
                self.assertEqual(r["lesson"], lesson)
                self.assertEqual(r["status"], "example_only")
                self.assertTrue(r["metrics"])
                self.assertTrue(r["stress_test"]["change"])
                self.assertTrue(r["stress_test"]["metrics"])
                self.assertTrue(r["details"])
                self.assertNotIn("scaffold", json.dumps(r))
                signatures.add(json.dumps(r["metrics"], sort_keys=True))
        self.assertEqual(len(signatures), 32)

    def test_results_are_deterministic(self):
        for lesson in IDS:
            with self.subTest(lesson=lesson):
                self.assertEqual(
                    self.results[lesson], run_experiment(lesson, *self.examples[lesson])
                )

    def test_changed_data_changes_actual_metrics_in_every_lesson(self):
        for lesson in IDS:
            with self.subTest(lesson=lesson):
                original, c = self.examples[lesson]
                d = copy.deepcopy(original)
                if lesson == "C01":
                    d["rows"][0]["label"] = 1 - d["rows"][0]["label"]
                elif lesson in {"C02", "S03", "S04", "S06", "S07", "S29", "S30"}:
                    d["rows"][0]["target"] += 10
                elif lesson in {"S01", "S05", "S08", "S09", "S10", "S13", "S14"}:
                    d["rows"][0]["label"] = 1 - d["rows"][0]["label"]
                elif lesson == "S02":
                    for row in d["rows"]:
                        row["available_day"] = 0
                elif lesson in {"S11", "S12"}:
                    d["rows"][0]["x1"] += 20
                elif lesson == "S15":
                    d["rows"][0]["pixels"] = (
                        np.array(d["rows"][0]["pixels"]) * 0
                    ).tolist()
                elif lesson == "S16":
                    d["rows"][0]["label"] = 1 - d["rows"][0]["label"]
                elif lesson in {"S17", "S18"}:
                    d["vectors"][0][0] += 3
                elif lesson in {"S19", "S20"}:
                    d["logits"][2][3] += 8
                elif lesson == "S21":
                    d["rows"][0]["responses"][c["candidate"]] = "unknown"
                elif lesson in {"S22", "S23"}:
                    d["queries"][0]["relevant"] = ["missing-document"]
                elif lesson == "S24":
                    d["rows"][0]["allowed"] = False
                elif lesson == "S25":
                    d["reward_probabilities"][0] = 0.95
                elif lesson in {"S26", "S27", "S28"}:
                    d["goal_reward"] = 2.0
                r = run_experiment(lesson, d, c)
                self.assertNotEqual(r["metrics"], self.results[lesson]["metrics"])
                self.assertNotEqual(
                    r["provenance"]["data_sha256"],
                    self.results[lesson]["provenance"]["data_sha256"],
                )

    def test_network_curves_include_training_and_validation(self):
        for lesson in ["S13", "S14"]:
            curve = self.results[lesson]["details"]["train_curve"]
            self.assertGreater(len(curve), 2)
            self.assertTrue(
                all(
                    "train_log_loss" in row and "validation_log_loss" in row
                    for row in curve
                )
            )
        r = self.results["S18"]
        self.assertLess(
            r["metrics"]["next_token_loss_after"],
            r["metrics"]["next_token_loss_before"],
        )

    def test_sequence_width_and_vocabulary_validation(self):
        d, c = load("S18")
        d["vectors"] = [row + [0.3, -0.2] for row in d["vectors"]]
        result = run_experiment("S18", d, c)
        self.assertEqual(result["metrics"]["trainable_head_parameters"], 24)
        self.assertEqual(
            result["stress_test"]["metrics"]["first_position_change_l2"], 0.0
        )
        d, c = load("S20")
        d["vocabulary"] = ["<unk>", "<eos>"]
        d["logits"] = [[0.0, 1.0], [1.0, 0.0]]
        with self.assertRaisesRegex(ValueError, "至少含3项"):
            run_experiment("S20", d, c)

    def test_policy_evaluation_and_transfer_use_comparable_data(self):
        result = self.results["S28"]
        detail = result["details"]
        self.assertTrue(
            set(detail["training_seeds"]).isdisjoint(detail["evaluation_seeds"])
        )
        self.assertEqual(len(detail["per_evaluation"]), 25)
        self.assertTrue(
            all(row["initial_state"] != 0 for row in detail["per_evaluation"])
        )
        comparison = self.results["S30"]["comparison"]
        self.assertEqual(
            comparison["old_on_adaptation_holdout"]["n"],
            comparison["adapted_on_first_half_of_new_batch"]["n"],
        )

    def test_unmasked_attention_is_permutation_equivariant(self):
        d, c = load("S17")
        c["causal"] = False
        r = run_experiment("S17", d, c)
        self.assertAlmostEqual(
            r["stress_test"]["metrics"]["aligned_output_change_l2"], 0.0, places=9
        )
        self.assertGreater(r["stress_test"]["metrics"]["output_change_l2"], 0.0)

    def test_saved_sampling_sequences_reproduce_all_aggregate_metrics(self):
        result = self.results["S20"]
        sequences = result["details"]["sample_ids"]
        m = result["metrics"]
        self.assertEqual(len(sequences), m["samples"])
        self.assertEqual(len({tuple(seq) for seq in sequences}), m["unique_sequences"])
        self.assertAlmostEqual(
            np.mean([len(seq) - 1 for seq in sequences]),
            m["mean_generated_length"],
            places=8,
        )
        self.assertAlmostEqual(
            np.mean([seq[-1] == 1 for seq in sequences]), m["end_token_rate"], places=8
        )
        self.assertAlmostEqual(
            np.mean([np.mean(np.diff(seq) == 0) for seq in sequences]),
            m["adjacent_repeat_rate"],
            places=8,
        )

    def test_input_errors_are_visible(self):
        d, c = load("S07")
        d["rows"][0].pop("x1")
        with self.assertRaisesRegex(ValueError, "缺少字段"):
            run_experiment("S07", d, c)
        d, c = load("S08")
        c["learning_rate"] = -1
        with self.assertRaises(ValueError):
            run_experiment("S08", d, c)
        d, c = load("S07")
        d["rows"][0]["target"] = float("nan")
        with self.assertRaises(ValueError):
            run_experiment("S07", d, c)
        d, c = load("S21")
        c["candidate"] = "not_executed_prompt"
        with self.assertRaisesRegex(ValueError, "响应"):
            run_experiment("S21", d, c)
        d, c = load("S07")
        d["rows"] = []
        with self.assertRaises(ValueError):
            run_experiment("S07", d, c)

    def test_cli_accepts_separate_input_and_output_paths(self):
        d, c = load("S07")
        c["ridge"] = 3.0
        with tempfile.TemporaryDirectory() as temporary:
            p = Path(temporary)
            (p / "data.json").write_text(json.dumps(d))
            (p / "config.json").write_text(json.dumps(c))
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "lesson-09/analysis.py"),
                    "--data",
                    str(p / "data.json"),
                    "--config",
                    str(p / "config.json"),
                    "--output",
                    str(p / "result"),
                ],
                cwd=p,
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            r = json.loads((p / "result/summary.json").read_text())
            self.assertEqual(r["config"]["ridge"], 3.0)
            self.assertFalse((p / "summary.json").exists())


if __name__ == "__main__":
    unittest.main()
