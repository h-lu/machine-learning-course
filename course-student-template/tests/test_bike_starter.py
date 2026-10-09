"""开放起点的边界测试；本测试不实际打开官方测试期标签。"""
from contextlib import redirect_stderr, redirect_stdout
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse import bike_starter as starter


class OpenStarterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # include_test=False：官方测试标签不解析或返回。
        cls.source = starter._read_source(ROOT, "data/bike/hour.csv")

    def test_reader_returns_only_real_development_rows_and_metadata_audit(self):
        train, validation, audit, metadata, test = self.source
        self.assertEqual((len(train), len(validation), len(metadata), len(test)), (13003, 2208, 17379, 0))
        self.assertTrue(all(row["datetime"] < "2012-07-01" for row in train))
        self.assertTrue(all("2012-07-01" <= row["datetime"] < "2012-10-01" for row in validation))
        self.assertEqual((audit["rows"], audit["columns"], audit["empty_fields"], audit["duplicate_hours"]), (17379, 17, 0, 0))
        self.assertEqual((audit["expected_calendar_hours"], audit["absent_timestamp_rows"]), (17544, 165))
        self.assertEqual(sum(row["missing_hours"] for row in audit["monthly_coverage"]), 165)
        self.assertEqual(set(train[0]), set(starter.SOURCE_FIELDS) | {"datetime"})
        self.assertIsInstance(train[0]["temp"], float)
        self.assertIsInstance(train[0]["cnt"], int)
        self.assertIsInstance(train[0]["datetime"], str)
        self.assertTrue(all(set(row) == {"instant", "datetime", "hr", "partition"} for row in metadata))
        self.assertFalse(any("mean" in key or "mae" in key or "quantile" in key for key in audit))

    def run_main(self, root, lesson, config, extra_args=()):
        lesson_dir = root / f"lesson-{lesson:02d}"
        lesson_dir.mkdir(parents=True, exist_ok=True)
        (lesson_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
        with patch.object(starter, "_read_source", return_value=self.source), patch.object(sys, "argv", ["analysis.py", *extra_args]), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            starter.main(lesson_dir, lesson)
        output = lesson_dir / "artifacts/starter"
        return output

    def test_default_main_prepares_no_course_pipeline_or_candidate_menu(self):
        with tempfile.TemporaryDirectory(prefix="open-bike-starter-") as temp:
            root = Path(temp)
            for lesson in range(1, 8):
                with self.subTest(lesson=lesson):
                    output = self.run_main(root, lesson, {"my_method": "anything I choose", "my_important_decisions": ["loss", "inputs"]})
                    summary = json.loads((output / "summary.json").read_text())
                    self.assertEqual(summary["status"], "not_started")
                    self.assertNotIn("metrics", summary)
                    self.assertFalse((output / "records.csv").exists())
                    self.assertFalse((output / "model.json").exists())
                    self.assertFalse((output / "selection_plan.json").exists())
                    self.assertFalse((output / "alerts.csv").exists())
                    self.assertEqual((output / "baseline.json").exists(), lesson == 2)
                    with (output / "sample.csv").open(newline="") as stream:
                        rows = list(csv.DictReader(stream))
                    self.assertEqual(len(rows), 12)
                    self.assertTrue(all(row["datetime"] < "2012-10-01" for row in rows))
                    if lesson in (4, 5):
                        self.assertTrue(all("cnt" not in row and "casual" not in row and "registered" not in row for row in rows))
            baseline = json.loads((root / "lesson-02/artifacts/starter/baseline.json").read_text())
            self.assertEqual((baseline["training_rows"], baseline["validation_rows"], baseline["mae_denominator"]), (13003, 2208, 2208))
            self.assertAlmostEqual(baseline["validation_mae"], 197.82937894348797)

    def test_explicit_output_protected_default_rebuilt_and_stale_baseline_removed(self):
        with tempfile.TemporaryDirectory(prefix="open-bike-output-") as temp:
            root = Path(temp)
            output = self.run_main(root, 1, {"starter_baseline": True})
            self.assertTrue((output / "baseline.json").exists())
            output = self.run_main(root, 1, {})
            self.assertFalse((output / "baseline.json").exists())
            before = {path.name: path.read_bytes() for path in output.iterdir()}
            self.run_main(root, 1, {})
            self.assertEqual(before, {path.name: path.read_bytes() for path in output.iterdir()})
            with self.assertRaises(SystemExit) as error:
                self.run_main(root, 1, {}, ("--output", "lesson-01/artifacts/starter"))
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(before, {path.name: path.read_bytes() for path in output.iterdir()})
            self.run_main(root, 1, {}, ("--config", "lesson-01/config.json", "--output", "lesson-01/artifacts/fresh"))
            fresh = root / "lesson-01/artifacts/fresh"
            self.assertEqual(before, {path.name: path.read_bytes() for path in fresh.iterdir()})

    def test_optional_manual_example_is_three_rows_not_full_validation_answer(self):
        with tempfile.TemporaryDirectory(prefix="open-bike-manual-") as temp:
            output = self.run_main(Path(temp), 1, {"intercept": 30, "slope": 300})
            with (output / "manual_sample.csv").open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 3)
            self.assertFalse((output / "records.csv").exists())
            for row in rows:
                self.assertAlmostEqual(float(row["prediction"]), 30 + 300 * float(row["temp"]))

    def test_thin_math_and_arbitrary_result_format(self):
        self.assertEqual(starter.mae([10, 20, 30], [12, 17, 34]), 3)
        intercept, slope = starter.fit_simple_line([0, 1, 2], [4, 7, 10])
        self.assertAlmostEqual(intercept, 4)
        self.assertAlmostEqual(slope, 3)
        for actual, predicted in (([], []), ([1], [1, 2]), ([float("nan")], [1])):
            with self.subTest(actual=actual), self.assertRaises(ValueError):
                starter.mae(actual, predicted)
        with self.assertRaises(ValueError):
            starter.fit_simple_line([1, 1], [2, 3])
        with tempfile.TemporaryDirectory(prefix="open-bike-save-") as temp:
            output = Path(temp) / "my-results"
            records = [{"my_sample": "a", "my_decision": "I chose a new method", "my_score": 3}]
            summary = {"my_method": "not in any menu", "my_evidence": "an independent calculation"}
            starter.save_results(output, records, summary)
            self.assertEqual(json.loads((output / "summary.json").read_text()), summary)
            with self.assertRaises(ValueError):
                starter.save_results(output, records, summary)

    def test_default_reader_does_not_parse_sealed_target_even_if_it_is_unparseable(self):
        # 故意不使用官方test标签。小fixture的sealed cnt为不可解析标记，默认reader仍应成功。
        with tempfile.TemporaryDirectory(prefix="open-bike-no-target-") as temp:
            root = Path(temp)
            fixture = root / "data/bike/hour.csv"
            fixture.parent.mkdir(parents=True)
            source_row = {field: str(value) for field, value in self.source[0][0].items() if field != "datetime"}
            rows = []
            for instant, date in ((1, "2011-01-01"), (2, "2012-07-01"), (3, "2012-10-01")):
                rows.append({**source_row, "instant": str(instant), "dteday": date, "hr": "0"})
            rows[-1]["cnt"] = "DO_NOT_PARSE_TEST_TARGET"
            starter.write_csv(fixture, rows, starter.SOURCE_FIELDS)
            with patch.object(starter.hashlib, "sha256") as digest:
                digest.return_value.hexdigest.return_value = starter.OFFICIAL_SHA256
                train, validation, audit = starter.load_development(root)
                self.assertEqual((len(train), len(validation), audit["sealed_test_rows"]), (1, 1, 1))
                self.assertTrue(all(row["datetime"] < "2012-10-01" for row in train + validation))

    def test_test_loader_requires_explicit_nonempty_decision_without_hard_method_schema(self):
        # 只mock fixture返回，不调用真实官方test标签读取。
        with tempfile.TemporaryDirectory(prefix="open-bike-test-protocol-") as temp:
            root = Path(temp)
            decision = root / "lesson-08/my-decision.md"
            with self.assertRaises(ValueError), patch.object(starter, "_read_source") as reader:
                starter.load_test(root, "lesson-08/my-decision.md")
            reader.assert_not_called()
            decision.parent.mkdir()
            decision.write_text(" ", encoding="utf-8")
            with self.assertRaises(ValueError), patch.object(starter, "_read_source") as reader:
                starter.load_test(root, "lesson-08/my-decision.md")
            reader.assert_not_called()
            decision.write_text("我保存了自己的方案、验证证据与预期；格式由我选择。", encoding="utf-8")
            fixture_test = [{"datetime": "2012-10-01T00:00", "cnt": 999}]
            with patch.object(starter, "_read_source", return_value=(*self.source[:4], fixture_test)) as reader:
                self.assertEqual(starter.load_selected_test(root, "lesson-08/my-decision.md"), fixture_test)
            reader.assert_called_once_with(root, "data/bike/hour.csv", include_test=True)


if __name__ == "__main__":
    unittest.main()
