"""C01–C02 的数值、输入、CLI 与完整提交检查；不替学生决定模型。"""
from __future__ import annotations

import copy
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.intro import example_config, example_data, fit_line, predict
from mlcourse.runtime import run_experiment


def run(lesson, data=None, config=None):
    return run_experiment(lesson, data or example_data(lesson), config or example_config(lesson))


class IntroMath(unittest.TestCase):
    def test_training_data_is_shared_and_source_is_synthetic(self):
        a, b = example_data("C01"), example_data("C02")
        self.assertEqual(a["rows"], [r for r in b["rows"] if r["split"] == "train"])
        self.assertEqual(len(a["rows"]), 8)
        self.assertEqual(len(b["rows"]), 18)
        self.assertIn("人工", a["source"])

    def test_c01_single_prediction_and_mean_error(self):
        result = run("C01")
        row = result["details"]["predictions"][2]
        self.assertEqual((row["queue_length"], row["actual"], row["prediction_rule"]), (2, 4, 5))
        self.assertEqual(row["absolute_error_rule"], 1)
        self.assertEqual(result["metrics"]["mae"], 1)

    def test_rule_does_not_fit_labels(self):
        data = example_data("C01")
        original = run("C01", data)
        data["rows"][0]["wait_minutes"] = 20
        modified = run("C01", data)
        self.assertEqual(original["details"]["prediction"], modified["details"]["prediction"])
        self.assertNotEqual(original["metrics"], modified["metrics"])

    def test_config_changes_rule_but_not_fitted_models(self):
        config = example_config("C02")
        before = run("C02", config=config)
        config["rule_slope"] = 1.5
        after = run("C02", config=config)
        self.assertNotEqual(before["comparison"]["rule"], after["comparison"]["rule"])
        self.assertEqual(before["comparison"]["baseline"], after["comparison"]["baseline"])
        self.assertEqual(before["metrics"], after["metrics"])

    def test_fitted_line_and_baseline_match_independent_hand_calculation(self):
        r = run("C02")
        self.assertEqual(r["details"]["model_coefficients"]["baseline"], [4, 0])
        self.assertEqual(r["details"]["coefficients"], [1, 2])
        self.assertAlmostEqual(r["metrics"]["mae"], 0.75)
        self.assertAlmostEqual(r["comparison"]["baseline"]["mae"], 1.25)

    def test_group_error_and_sample_counts(self):
        groups = run("C02")["details"]["by_period"]
        self.assertEqual(groups["午间"]["linear"]["n"], 3)
        self.assertEqual(groups["晚间"]["linear"]["n"], 1)
        self.assertEqual(groups["晚间"]["linear"]["mae"], 3)
        self.assertEqual(groups["晚间"]["baseline"]["mae"], 0)
        weighted = sum(g["linear"]["n"] * g["linear"]["mae"] for g in groups.values()) / 4
        self.assertEqual(weighted, 0.75)

    def test_test_set_is_opt_in_and_same_rows_for_every_model(self):
        self.assertEqual(run("C02")["details"]["evaluation_split"], "validation")
        config = example_config("C02"); config["evaluation_split"] = "test"
        r = run("C02", config=config)
        self.assertEqual(r["metrics"]["n"], 6)
        self.assertAlmostEqual(r["metrics"]["mae"], 2 / 3)
        self.assertAlmostEqual(r["comparison"]["baseline"]["mae"], 4 / 3)
        self.assertTrue(set(r["details"]["train_ids"]).isdisjoint(r["details"]["evaluation_ids"]))
        for row in r["details"]["predictions"]:
            for name in ("rule", "baseline", "linear"):
                self.assertAlmostEqual(row[f"absolute_error_{name}"], abs(row[f"prediction_{name}"] - row["actual"]))

    def test_validation_and_test_labels_never_change_training(self):
        data = example_data("C02")
        expected = run("C02", data)["details"]["model_coefficients"]
        for row in data["rows"]:
            if row["split"] != "train":
                row["wait_minutes"] += 100
        actual = run("C02", data)
        self.assertEqual(actual["details"]["model_coefficients"], expected)
        self.assertGreater(actual["metrics"]["mae"], 90)

    def test_training_labels_change_fitted_models(self):
        data = example_data("C02")
        expected = run("C02", data)["details"]["coefficients"]
        data["rows"][0]["wait_minutes"] += 10
        self.assertNotEqual(run("C02", data)["details"]["coefficients"], expected)

    def test_new_input_has_no_fabricated_label_or_error(self):
        for lesson in ("C01", "C02"):
            s = run(lesson)["stress_test"]["metrics"]
            self.assertTrue(s["outside_training_range"])
            self.assertIsNone(s["actual"])
            self.assertIsNone(s["mae"])
            self.assertEqual(s["predictions"]["rule"], 21)

    def test_invalid_inputs_are_rejected(self):
        for value in (-1, 1.5, None, True, "2", float("nan"), float("inf")):
            with self.subTest(value=value):
                data = example_data("C01"); data["rows"][0]["queue_length"] = value
                with self.assertRaises(ValueError): run_experiment("C01", data, example_config("C01"))
        for operation in ("duplicate", "empty", "missing", "split"):
            data = example_data("C01")
            if operation == "duplicate": data["rows"].append(copy.deepcopy(data["rows"][0]))
            elif operation == "empty": data["rows"] = []
            elif operation == "missing": del data["rows"][0]["wait_minutes"]
            else: data["rows"][0]["split"] = "trian"
            with self.assertRaises(ValueError): run_experiment("C01", data, example_config("C01"))

    def test_missing_evaluation_or_constant_training_feature_fails(self):
        data = example_data("C02")
        data["rows"] = [r for r in data["rows"] if r["split"] != "validation"]
        with self.assertRaisesRegex(ValueError, "没有 split=validation"):
            run("C02", data)
        data = example_data("C02")
        for row in data["rows"]:
            if row["split"] == "train": row["queue_length"] = 2
        with self.assertRaisesRegex(ValueError, "全相同"):
            run("C02", data)

    def test_seed_is_not_pretended_to_create_new_evidence(self):
        c = example_config("C02"); a = run("C02", config=c)
        c["seed"] = 101
        b = run("C02", config=c)
        self.assertEqual(a["metrics"], b["metrics"])
        self.assertEqual(a["details"], b["details"])


class IntroWorkflow(unittest.TestCase):
    def test_cli_writes_reproducible_json_csv_without_completing_submission(self):
        for n in (1, 2):
            folder = ROOT / f"lesson-{n:02d}"
            manifest_before = (folder / "submission.json").read_bytes()
            with tempfile.TemporaryDirectory() as temp:
                output = Path(temp)
                command = [sys.executable, str(folder / "analysis.py"), "--output", str(output)]
                subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
                first = {p.name: p.read_bytes() for p in output.iterdir()}
                subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
                self.assertEqual(first, {p.name: p.read_bytes() for p in output.iterdir()})
                payload = json.loads(first["summary.json"])
                self.assertEqual(payload["status"], "example_only")
                self.assertIn("mlcourse/intro.py", payload["provenance"]["source_sha256"])
                with (output / "predictions.csv").open() as f:
                    rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), payload["metrics"]["n"])
            self.assertEqual(manifest_before, (folder / "submission.json").read_bytes())

    def test_cli_alternate_files_and_test_split(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            (p / "data.json").write_text(json.dumps(example_data("C02")))
            (p / "config.json").write_text(json.dumps(example_config("C02")))
            command = [sys.executable, str(ROOT / "lesson-02/analysis.py"), "--data", "data.json",
                       "--config", "config.json", "--split", "test", "--output", "out"]
            subprocess.run(command, cwd=p, check=True, capture_output=True)
            result = json.loads((p / "out/summary.json").read_text())
            self.assertEqual(result["details"]["evaluation_split"], "test")
            self.assertEqual(result["metrics"]["n"], 6)

    def test_intro_data_generator_matches_committed_examples(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "new"
            subprocess.run([sys.executable, str(ROOT / "scripts/build_example_data.py"), "--output", str(destination)],
                           cwd=ROOT, check=True, capture_output=True)
            for n in (1, 2):
                for file in ("data/base.json", "config.json"):
                    self.assertEqual(json.loads((destination/f"lesson-{n:02d}"/file).read_text()),
                                     json.loads((ROOT/f"lesson-{n:02d}"/file).read_text()))
                self.assertEqual((destination/f"lesson-{n:02d}/analysis.py").read_bytes(),
                                 (ROOT/f"lesson-{n:02d}/analysis.py").read_bytes())

    def test_completed_intro_submissions_reproduce_through_course_ci(self):
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            scratch = Path(temp) / "student"
            shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(".git", "__pycache__", "artifacts", ".venv"))
            for n in (1, 2):
                folder = scratch / f"lesson-{n:02d}"
                if n == 2:
                    c = json.loads((folder / "config.json").read_text())
                    c["evaluation_split"] = "test"
                    (folder / "config.json").write_text(json.dumps(c))
                subprocess.run([sys.executable, "scripts/course.py", "run", str(n)], cwd=scratch, check=True, capture_output=True)
                manifest = json.loads((folder / "submission.json").read_text())
                manifest["status"] = "complete"
                (folder / "submission.json").write_text(json.dumps(manifest))
                (folder / "report.md").write_text("测试报告：核对取餐预测与误差，结果仅支持教学例子。")
            subprocess.run([sys.executable, "scripts/course.py", "ci"], cwd=scratch, check=True, capture_output=True)

    def test_readme_keeps_seven_sections_and_shared_terminology(self):
        import re
        expected = ["本课要解决什么问题", "本课要学会什么", "90 分钟安排", "完成步骤", "必须提交什么", "不同起点怎么做", "运行限制"]
        for n in (1, 2):
            text = (ROOT/f"lesson-{n:02d}/README.md").read_text()
            self.assertEqual(re.findall(r"^## (.+)$", text, re.M), expected)
        text = (ROOT/"docs/TERMINOLOGY.md").read_text()
        for term in ("特征", "标签", "基线模型", "训练集", "验证集", "测试集", "平均绝对误差"):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
