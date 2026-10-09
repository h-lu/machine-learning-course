"""Exercise student-defined controls through lesson08 using synthetic data only."""
from contextlib import redirect_stderr, redirect_stdout
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

STUDENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDENT))
from mlcourse import bike_starter as starter


class CustomLesson08Methods(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lesson08-custom-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in ("lesson-08/analysis.py", "mlcourse/bike_starter.py"):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(STUDENT / relative, target)
        spec = importlib.util.spec_from_file_location("fixture_lesson08", self.root / "lesson-08/analysis.py")
        self.analysis = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.analysis)
        self.train = [self.row(day, hour) for day in ("2012-06-04", "2012-06-05") for hour in range(24)]
        self.validation = [self.row("2012-07-02", hour) for hour in (6, 8, 12, 17)]
        self.test = [self.row("2012-10-02", hour) for hour in (0, 8, 17, 23)]
        self.audit = {"fixture": "artificial hourly shape, not Bike observations",
                      "data_sha256": hashlib.sha256(json.dumps(self.train).encode()).hexdigest()}
        (self.root / "lesson-08/plan.md").write_text(
            "人工夹具：比较线性小时项与小时指示变量；相同训练记录和最小二乘算法，只改小时表示。\n",
            encoding="utf-8")
        self.analysis.candidate_predictions = self.student_methods

    @staticmethod
    def row(day, hour):
        count = 20 + 2 * hour + 100 * int(hour in (8, 17))
        return {"dteday": day, "datetime": f"{day}T{hour:02d}:00", "season": 2,
                "yr": 1, "mnth": int(day[5:7]), "hr": hour, "holiday": 0,
                "weekday": 1, "workingday": 1, "weathersit": 1,
                "temp": .4, "atemp": .4, "hum": .5, "windspeed": .2,
                "cnt": count, "casual": 0, "registered": count, "instant": hour + 1}

    def student_methods(self, train_inputs, train_targets, evaluation_inputs):
        # A student-written matched pair: same least squares, intercept, rows,
        # and target; only the hour representation changes. No answer fields.
        for rows in (train_inputs, evaluation_inputs):
            self.assertTrue(all({"cnt", "casual", "registered", "instant"}.isdisjoint(row) for row in rows))
        train_hours = np.asarray([row["hr"] for row in train_inputs])
        evaluation_hours = np.asarray([row["hr"] for row in evaluation_inputs])
        result = {}
        for name, indicators in (("my_linear_hour_control", False), ("my_hour_indicator_candidate", True)):
            def design(hours):
                columns = (hours[:, None] == np.arange(1, 24)).astype(float) if indicators else hours[:, None]
                return np.column_stack((np.ones(len(hours)), columns))
            weights = np.linalg.lstsq(design(train_hours), np.asarray(train_targets), rcond=None)[0]
            result[name] = np.maximum(0, design(evaluation_hours) @ weights)
        return result

    def run_entry(self, args, allow_test=False):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(self.analysis, "load_development", return_value=(self.train, self.validation, self.audit)), \
             patch.object(starter, "_read_source", side_effect=AssertionError("No real CSV may be read")), \
             patch.object(starter, "load_selected_test", return_value=self.test) as test_loader, \
             redirect_stdout(stdout), redirect_stderr(stderr):
            code = self.analysis.main(args)
            if allow_test:
                test_loader.assert_called_once()
            else:
                test_loader.assert_not_called()
        return code, stdout.getvalue(), stderr.getvalue()

    def result_rows(self, output, name):
        with (self.root / output / name).open(encoding="utf-8", newline="") as stream:
            return list(csv.DictReader(stream))

    def validation_run(self):
        output = "lesson-08/artifacts/custom-validation"
        code, stdout, stderr = self.run_entry(["--plan", "lesson-08/plan.md", "--output", output])
        self.assertEqual(code, 0, stdout + stderr)
        return output

    def test_validation_reports_matched_student_control_and_candidate(self):
        output = self.validation_run()
        comparison = self.result_rows(output, "comparison.csv")
        self.assertEqual({row["method"] for row in comparison},
                         {"baseline", "my_linear_hour_control", "my_hour_indicator_candidate"})
        records = self.result_rows(output, "records.csv")
        self.assertEqual(len(records), 3 * len(self.validation))
        for score in comparison:
            selected = [row for row in records if row["method"] == score["method"]]
            self.assertEqual({row["datetime"] for row in selected}, {row["datetime"] for row in self.validation})
            scalar_mae = sum(abs(float(row["prediction"]) - float(row["cnt"])) for row in selected) / len(selected)
            self.assertAlmostEqual(float(score["mae"]), scalar_mae)
        candidate = next(row for row in comparison if row["method"] == "my_hour_indicator_candidate")
        self.assertAlmostEqual(float(candidate["mae"]), 0, places=9)

    def test_final_test_reports_only_either_preselected_custom_method(self):
        self.validation_run()
        for name in ("my_linear_hour_control", "my_hour_indicator_candidate"):
            with self.subTest(selected=name):
                decision = f"lesson-08/decision-{name}.md"
                (self.root / decision).write_text(f"测试前选择：{name}；依据已保存的人工验证比较。\n", encoding="utf-8")
                output = f"lesson-08/artifacts/test-{name}"
                args = ["--split", "test", "--plan", "lesson-08/plan.md", "--decision", decision,
                        "--selected-method", name, "--output", output]
                code, stdout, stderr = self.run_entry(args, allow_test=True)
                self.assertEqual(code, 0, stdout + stderr)
                self.assertIn(f"所选方法={name}", stdout)
                self.assertNotIn("训练均值基线=", stdout)
                comparison = self.result_rows(output, "comparison.csv")
                records = self.result_rows(output, "records.csv")
                summary = json.loads((self.root / output / "summary.json").read_text())
                for rows in (comparison, records, summary["metrics"]):
                    self.assertEqual({row["method"] for row in rows}, {name})
                    self.assertEqual({row["split"] for row in rows}, {"test"})
                self.assertEqual(len(records), len(self.test))

    def test_missing_test_choice_does_not_read_any_test_data(self):
        code, stdout, stderr = self.run_entry(["--split", "test", "--output", "lesson-08/artifacts/no-choice"])
        self.assertEqual(code, 2, stdout + stderr)
        self.assertFalse((self.root / "lesson-08/artifacts/no-choice").exists())


if __name__ == "__main__":
    unittest.main()
