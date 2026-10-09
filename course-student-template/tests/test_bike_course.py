"""真实数据的计算/边界验收，不把默认分数当学生答案。"""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse import bike_course as bike


class BikeCourseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.audit = bike._read_rows(ROOT / "data/bike/hour.csv")

    def run_course(self, lesson, config=None, rows=None, root=ROOT):
        with patch.object(bike, "_read_rows", return_value=(rows or self.rows, self.audit)):
            return bike.run_lesson(root, lesson, config or {})

    def test_official_file_counts_and_calendar_accounting(self):
        result = self.run_course(4)
        audit = result["audit.json"]
        self.assertEqual((audit["rows"], audit["columns"], audit["empty_fields"], audit["duplicate_hours"]),
                         (17379, 17, 0, 0))
        self.assertEqual(audit["data_sha256"], bike.OFFICIAL_SHA256)
        self.assertEqual((audit["expected_calendar_hours"], audit["absent_timestamp_rows"]), (17544, 165))
        for name in ("coverage_month.csv", "coverage_hour.csv"):
            values = result[name]
            self.assertEqual(sum(row["expected_hours"] for row in values), 17544)
            self.assertEqual(sum(row["observed_rows"] for row in values), 17379)
            self.assertEqual(sum(row["missing_hours"] for row in values), 165)
        self.assertEqual(len(result["missing_hours.csv"]), 165)
        self.assertEqual(len(result["records.csv"]), 17379)
        self.assertTrue(all("cnt" not in row for row in result["records.csv"]))
        summary = result["summary.json"]
        self.assertEqual((summary["training_rows"], summary["validation_rows"], summary["sealed_test_rows"]),
                         (13003, 2208, 2168))

    def test_manual_rule_and_mae_can_be_recalculated_from_each_row(self):
        result = self.run_course(1, {"intercept": 0.0, "slope": 0.0})
        records = result["records.csv"]
        self.assertEqual(len(records), 2208)
        self.assertTrue(all(row["prediction"] == 0 for row in records))
        # 零预测时 MAE 必须等于这2208条真实非负需求均值，这是独立的性质。
        actual_total = math.fsum(row["cnt"] for row in self.rows if bike.TRAIN_END <= row["datetime"] < bike.VALIDATION_END)
        metrics = result["summary.json"]["metrics"]["manual_rule"]
        self.assertAlmostEqual(metrics["mae"], actual_total / 2208, places=10)
        self.assertEqual(metrics["mae_denominator"], 2208)
        custom = self.run_course(1, {"intercept": 30.0, "slope": 300.0})["trace.csv"]
        self.assertEqual(len(custom), 12)
        for row in custom:
            self.assertAlmostEqual(row["prediction"], 30 + 300 * row["temp"])
            self.assertAlmostEqual(row["signed_error"], row["prediction"] - row["cnt"])
            self.assertAlmostEqual(row["absolute_error"], abs(row["signed_error"]))

    def test_selected_method_and_baseline_use_identical_validation_samples(self):
        result = self.run_course(2)
        selected = [r for r in result["records.csv"] if r["method"] == "temp_linear"]
        baseline = [r for r in result["records.csv"] if r["method"] == "mean"]
        self.assertEqual([r["instant"] for r in selected], [r["instant"] for r in baseline])
        self.assertEqual(len(selected), 2208)
        training = [row for row in self.rows if row["datetime"] < bike.TRAIN_END]
        independent_mean = math.fsum(row["cnt"] for row in training) / len(training)
        self.assertTrue(all(abs(r["prediction"] - independent_mean) < 1e-10 for r in baseline))
        # 含截距的训练最小二乘残差须与常数列/温度列正交，不以复制拟合公式验收。
        model = result["model.json"]["models"]["temp_linear"]
        residuals = [(model["intercept"] + model["slope"] * row["temp"] - row["cnt"]) for row in training]
        self.assertAlmostEqual(math.fsum(residuals), 0.0, places=6)
        self.assertAlmostEqual(math.fsum(error * row["temp"] for error, row in zip(residuals, training)), 0.0, places=6)
        mean_only = self.run_course(2, {"method": "mean"})
        self.assertEqual(len(mean_only["records.csv"]), 2208)
        self.assertEqual(set(mean_only["summary.json"]["metrics"]), {"mean"})

    def test_purpose_and_input_availability_reject_label_leakage(self):
        for field in ("cnt", "casual", "registered", "instant", "dteday", "yr"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.run_course(3, {"input_fields": ["temp", field]})
        with self.assertRaises(ValueError):
            self.run_course(3, {"purpose": "day_ahead_schedule"})
        day_ahead = self.run_course(3, {"purpose": "day_ahead_schedule", "input_fields": ["hr", "workingday"],
                                      "rule_field": "hr", "intercept": 0, "slope": 15})
        self.assertEqual(day_ahead["model.json"]["used_inputs"], ["hr"])
        result = self.run_course(3)
        counts = result["summary.json"]["decision_counts"]
        self.assertEqual(sum(counts[key] for key in ("true_positive", "false_positive", "false_negative", "true_negative")), 2208)
        self.assertEqual(counts["precision_denominator"], len(result["alerts.csv"]))
        self.assertEqual(counts["recall_denominator"], sum(row["cnt"] >= 200 for row in result["records.csv"]))

    def test_random_split_never_opens_sealed_test_and_keeps_sample_size(self):
        time = self.run_course(5)
        random = self.run_course(5, {"split": "random", "seed": 17})
        for result in (time, random):
            manifest = result["split_manifest.csv"]
            self.assertEqual(len({row["instant"] for row in manifest}), 15211)
            self.assertEqual(sum(row["partition"] == "train" for row in manifest), 13003)
            self.assertEqual(sum(row["partition"] == "validation" for row in manifest), 2208)
            self.assertTrue(all(row["datetime"] < "2012-10-01" for row in manifest))
            self.assertFalse(any(name.startswith("INVALID") for name in result))
        self.assertNotEqual(time["split_manifest.csv"], random["split_manifest.csv"])
        self.assertTrue(any(row["partition"] == "train" and row["datetime"] >= "2012-07-01" for row in random["split_manifest.csv"]))
        invalid = self.run_course(5, {"leakage_demo": True})
        self.assertFalse(invalid["INVALID_leakage_demo.json"]["valid_experiment"])
        self.assertFalse(invalid["INVALID_leakage_demo.json"]["included_in_legal_metrics"])
        self.assertNotIn("INVALID_target_sum_leakage", invalid["summary.json"]["metrics"])

    def test_daily_capacity_and_weighted_error_denominators(self):
        result = self.run_course(6, {"daily_capacity": 2, "alert_threshold": 0, "underestimate_weight": 3})
        records = result["records.csv"]
        self.assertTrue(all(row["selected"] <= 2 and row["selected"] == min(row["candidates"], 2)
                            for row in result["daily_capacity.csv"]))
        self.assertEqual(sum(row["selected"] for row in result["daily_capacity.csv"]), sum(r["final_alert"] for r in records))
        independent = math.fsum((r["cnt"] - r["prediction"]) * 3 if r["cnt"] > r["prediction"]
                               else r["prediction"] - r["cnt"] for r in records) / len(records)
        metrics = result["summary.json"]["metrics"]["hour_mean"]
        self.assertAlmostEqual(metrics["weighted_mae"], independent, places=10)
        self.assertEqual(metrics["weighted_mae_denominator"], 2208)
        no_alerts = self.run_course(6, {"alert_threshold": 1000000})
        counts = no_alerts["summary.json"]["decision_counts"]
        self.assertIsNone(counts["precision"])
        self.assertIsNone(counts["recall"])
        self.assertEqual(counts["precision_denominator"], 0)
        self.assertEqual(counts["true_negative"], 2208)

    def test_select_plan_is_label_free_and_budgeted_before_reveal(self):
        result = self.run_course(7)
        plan = result["selection_plan.json"]
        self.assertFalse(result["summary.json"]["labels_revealed"])
        self.assertNotIn("metrics", result["summary.json"])
        self.assertTrue(all("cnt" not in row for row in result["records.csv"]))
        train_ids = {row["instant"] for row in self.rows if row["datetime"] < bike.TRAIN_END}
        self.assertEqual(len(plan["scenarios"]), 3)
        for scenario in plan["scenarios"]:
            initial = set(scenario["initial_ids"])
            self.assertEqual(len(initial), 240)
            self.assertEqual(scenario["pool_size"], 13003 - 240)
            for selected in scenario["selections"].values():
                self.assertEqual(len(set(selected)), 120)
                self.assertFalse(initial & set(selected))
                self.assertTrue((initial | set(selected)) <= train_ids)
        # 选择不得依赖训练标签：打乱标签，计划应逐字段保持相同。
        changed = deepcopy(self.rows)
        for row in changed:
            row["cnt"] = 999999 - row["cnt"]
        self.assertEqual(plan, self.run_course(7, rows=changed)["selection_plan.json"])

    def test_reveal_requires_saved_identical_plan_and_retains_all_seeds(self):
        with tempfile.TemporaryDirectory(prefix="bike-course-test-") as temp:
            root = Path(temp)
            plan_path = root / "lesson-07/artifacts/select/selection_plan.json"
            config = {"stage": "reveal"}
            with self.assertRaises(ValueError):
                self.run_course(7, config, root=root)
            plan = self.run_course(7)["selection_plan.json"]
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(bike._json_text(plan), encoding="utf-8")
            revealed = self.run_course(7, config, root=root)
            learning = revealed["learning_curve.csv"]
            self.assertEqual(len(learning), 12)
            self.assertEqual({r["seed"] for r in learning}, {11, 29, 47})
            self.assertTrue(all(r["validation_rows"] == 2208 and r["training_rows"] == 240 + r["budget_used"] for r in learning))
            self.assertTrue(all(r["datetime"] < "2012-07-01" for r in revealed["revealed_training.csv"]))
            self.assertTrue(all(r["datetime"] < "2012-10-01" for r in revealed["records.csv"]))
            tampered = deepcopy(plan)
            tampered["scenarios"][0]["selections"]["random"][0] = 17379
            plan_path.write_text(bike._json_text(tampered), encoding="utf-8")
            with self.assertRaises(ValueError):
                self.run_course(7, config, root=root)

    def test_all_development_experiments_are_invariant_to_sealed_targets(self):
        changed = deepcopy(self.rows)
        for row in changed:
            if row["datetime"] >= bike.VALIDATION_END:
                row["cnt"] = 1000000 + row["instant"]
                row["casual"] = row["cnt"]
                row["registered"] = 0
        for lesson in range(1, 8):
            with self.subTest(lesson=lesson):
                self.assertEqual(self.run_course(lesson), self.run_course(lesson, rows=changed))

    def test_bad_config_and_test_options_fail_explicitly(self):
        bad = [(1, {"slope": float("nan")}), (1, {"inspect_count": True}),
               (2, {"method": []}), (3, {"purpose": []}), (3, {"rule_field": []}),
               (5, {"test": True}), (5, {"split": []}), (6, {"daily_capacity": 0}),
               (7, {"stage": []}), (7, {"seeds": [11, 11]}), (7, {"selection_note": "太短"})]
        for lesson, config in bad:
            with self.subTest(lesson=lesson, config=config), self.assertRaises(ValueError):
                self.run_course(lesson, config)

    def test_cli_default_rebuild_and_explicit_existing_output_protection(self):
        with tempfile.TemporaryDirectory(prefix="bike-course-cli-") as temp:
            root = Path(temp)
            lesson_dir = root / "lesson-01"
            lesson_dir.mkdir()
            (lesson_dir / "config.json").write_text("{}", encoding="utf-8")
            with patch.object(bike, "_read_rows", return_value=(self.rows, self.audit)), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                with patch.object(sys, "argv", ["analysis.py"]):
                    bike.main(lesson_dir, 1)
                    first = {p.name: p.read_bytes() for p in (lesson_dir / "artifacts/run").iterdir()}
                    bike.main(lesson_dir, 1)
                    second = {p.name: p.read_bytes() for p in (lesson_dir / "artifacts/run").iterdir()}
                self.assertEqual(first, second)
                with patch.object(sys, "argv", ["analysis.py", "--output", "artifacts/run"]), self.assertRaises(SystemExit) as error:
                    bike.main(lesson_dir, 1)
                self.assertEqual(error.exception.code, 2)
                self.assertEqual(first, {p.name: p.read_bytes() for p in (lesson_dir / "artifacts/run").iterdir()})
                with patch.object(sys, "argv", ["analysis.py", "--config", "lesson-01/config.json", "--output", "lesson-01/artifacts/trial"]):
                    bike.main(lesson_dir, 1)
                self.assertEqual(first, {p.name: p.read_bytes() for p in (lesson_dir / "artifacts/trial").iterdir()})


if __name__ == "__main__":
    unittest.main()
