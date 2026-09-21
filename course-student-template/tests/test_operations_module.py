"""S25–S30 同一服务台作品的机制、边界与学生命令测试。"""

from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mlcourse.operations import run


def load(number: int) -> tuple[dict, dict]:
    folder = ROOT / f"lesson-{number:02d}"
    data = json.loads((folder / "data/base.json").read_text(encoding="utf-8"))
    config = json.loads((folder / "config-support.json").read_text(encoding="utf-8"))
    return data, config


def load_s30_final() -> tuple[dict, dict]:
    data, config = load(32)
    final = json.loads((ROOT / "lesson-32/data/final.json").read_text(encoding="utf-8"))
    data.update({key: value for key, value in final.items() if key not in {"kind", "project_id", "source"}})
    return data, config


class OperationsMechanisms(unittest.TestCase):
    def test_six_lessons_keep_one_project_and_identical_base_data(self):
        contents = [(ROOT / f"lesson-{number:02d}/data/base.json").read_bytes() for number in range(27, 33)]
        self.assertTrue(all(item == contents[0] for item in contents[1:]))
        data, _ = load(27)
        self.assertEqual(data["project_id"], "equipment-helpdesk-v1")

    def test_s25_never_reveals_unchosen_feedback_to_policy_output(self):
        data, config = load(27)
        result, tables = run("S25", data, config)
        self.assertTrue(all(row["other_response_feedback"] == "未观察" for row in tables["rounds"]))
        self.assertEqual(result["denominator"]["rounds_per_episode"], 16)
        self.assertGreater(
            result["comparison"]["epsilon"]["mean_response_types_tried"],
            result["comparison"]["greedy"]["mean_response_types_tried"],
        )

    def test_s26_short_and_long_term_scores_select_different_policies(self):
        data, config = load(28)
        result, tables = run("S26", data, config)
        self.assertEqual(result["comparison"]["speed_score"]["selected_policy"], "fast_auto")
        self.assertEqual(result["comparison"]["long_term_score"]["selected_policy"], "risk_aware")
        q02 = [row for row in tables["trajectories"] if row["id"] == "Q02"]
        self.assertEqual(next(row for row in q02 if row["policy"] == "fast_auto")["long_term_score"], -3)
        self.assertEqual(next(row for row in q02 if row["policy"] == "risk_aware")["long_term_score"], 0.5)

    def test_s27_uses_only_arrived_labels_and_keeps_unknown_rows_unknown(self):
        data, config = load(29)
        result, tables = run("S27", data, config)
        current = result["batches"]["current"]
        self.assertEqual((current["known_correct"], current["labeled_n"], current["unlabeled_n"]), (2, 4, 2))
        unknown = [row for row in tables["monitoring_records"] if not row["label_available"]]
        self.assertTrue(all(row["known_correct"] == "尚不能判断" for row in unknown))
        self.assertTrue(result["alarms"]["before_labels"])
        self.assertTrue(result["alarms"]["after_available_labels"])

    def test_s28_separates_quality_cache_and_estimated_cost(self):
        data, config = load(30)
        result, tables = run("S28", data, config)
        rows = {(row["profile"], row["cache_enabled"]): row for row in result["deterministic_comparison"]}
        self.assertEqual(rows[("fast", False)]["correct"], 8)
        self.assertEqual(rows[("thorough", False)]["correct"], 10)
        self.assertEqual(rows[("fast", True)]["cache_hits"], 2)
        self.assertEqual(rows[("fast", True)]["estimated_cost_units"], 8)
        self.assertTrue(all(row["fresh_compute_ms"] >= 0 for row in tables["timings"]))
        self.assertTrue(all(row["total_elapsed_ms"] >= 0 for row in tables["timings"]))
        self.assertTrue(all(row["mean_request_latency_ms"] >= 0 for row in tables["timings"]))
        self.assertTrue(all("request_latency_ms" not in row for row in tables["records"]))

        personal_config = json.loads((ROOT / "lesson-30/config-check.json").read_text(encoding="utf-8"))
        personal_result, personal_tables = run("S28", data, personal_config)
        changed = {
            (row["profile"], row["cache_enabled"]): row
            for row in personal_result["repeat_input_check"]["comparison_after_change"]
        }
        self.assertEqual(changed[("fast", True)]["cache_hits"], 1)
        self.assertEqual(changed[("thorough", True)]["cache_hits"], 1)
        self.assertIn("changed_records", personal_tables)
        self.assertTrue(all("request_latency_ms" not in row for row in personal_tables["changed_records"]))

    def test_s29_retests_both_schemes_on_the_same_new_rows(self):
        data, config = load(31)
        result, tables = run("S29", data, config)
        self.assertEqual(result["comparison"]["original"], {"correct": 6, "n": 8})
        self.assertEqual(result["comparison"]["adapted"], {"correct": 8, "n": 8})
        self.assertEqual(len(tables["transfer_records"]), 8)

        personal = json.loads((ROOT / "lesson-31/config.json").read_text(encoding="utf-8"))
        personal_result, personal_tables = run("S29", data, personal)
        self.assertEqual(personal_result["provided_comparison"], result["comparison"])
        self.assertEqual(personal_result["comparison"]["original"]["n"], 9)
        self.assertEqual(personal_result["comparison"]["adapted"]["n"], 9)
        self.assertEqual(len(personal_tables["transfer_records"]), 9)

    def test_s30_final_comparison_has_equal_denominators(self):
        data, config = load_s30_final()
        result, tables = run("S30", data, config)
        self.assertEqual(result["evaluation_stage"], "final_evaluation")
        self.assertEqual(result["final_evaluation"]["original"]["n"], 8)
        self.assertEqual(result["final_evaluation"]["adapted"]["n"], 8)
        self.assertEqual(result["changed_request_ids"], ["D01", "D02", "D06"])
        self.assertEqual(len(tables["delivery_records"]), 8)


class OperationsColdReadCommands(unittest.TestCase):
    def test_each_support_command_writes_documented_files(self):
        expected = {
            27: ["summary.json", "rounds.csv", "episodes.csv"],
            28: ["summary.json", "trajectories.csv"],
            29: ["summary.json", "records.csv", "batch_metrics.csv"],
            30: ["summary.json", "records.csv", "timings.csv"],
            31: ["summary.json", "records.csv"],
            32: ["summary.json", "records.csv", "manifest.json"],
        }
        with tempfile.TemporaryDirectory() as temporary:
            for number, names in expected.items():
                output = Path(temporary) / str(number)
                command = [
                    sys.executable,
                    str(ROOT / f"lesson-{number:02d}/analysis.py"),
                    "--config",
                    str(ROOT / f"lesson-{number:02d}/config-support.json"),
                    "--output",
                    str(output),
                ]
                completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                for name in names:
                    self.assertTrue((output / name).is_file(), f"lesson-{number:02d} missing {name}")
                if number == 32:
                    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
                    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
                    self.assertEqual(summary["evaluation_stage"], "development")
                    self.assertEqual(manifest["evaluation_stage"], "development")
                    self.assertIsInstance(manifest["run_command"], list)
                    self.assertIn("--config", manifest["run_command"])
                    self.assertNotIn("--final-data", manifest["run_command"])
                    self.assertNotIn("final_data_sha256", manifest)
                    self.assertIn("--output", manifest["run_command"])
                    output_index = manifest["run_command"].index("--output")
                    self.assertEqual(manifest["run_command"][output_index + 1], "<OUTPUT_DIR>")
                    for name in ("summary.json", "records.csv"):
                        digest = hashlib.sha256((output / name).read_bytes()).hexdigest()
                        self.assertEqual(manifest["output_sha256"][name], digest)

    def test_s28_records_are_deterministic_while_timings_may_vary(self):
        with tempfile.TemporaryDirectory() as temporary:
            outputs = [Path(temporary) / name for name in ("first", "second")]
            for output in outputs:
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "lesson-30/analysis.py"),
                        "--config", str(ROOT / "lesson-30/config-support.json"),
                        "--output", str(output),
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                (outputs[0] / "records.csv").read_bytes(),
                (outputs[1] / "records.csv").read_bytes(),
            )
            self.assertEqual(
                (outputs[0] / "summary.json").read_bytes(),
                (outputs[1] / "summary.json").read_bytes(),
            )

    def test_s30_manifest_is_independent_of_output_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            outputs = [Path(temporary) / name for name in ("first", "second")]
            for output in outputs:
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "lesson-32/analysis.py"),
                        "--data", str(ROOT / "lesson-32/data/base.json"),
                        "--final-data", str(ROOT / "lesson-32/data/final.json"),
                        "--config", str(ROOT / "lesson-32/config.json"),
                        "--output", str(output),
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                (outputs[0] / "manifest.json").read_bytes(),
                (outputs[1] / "manifest.json").read_bytes(),
            )

    def test_s30_release_candidate_changes_selected_evaluation(self):
        data, config = load_s30_final()
        adapted, _ = run("S30", data, config)
        config["release_candidate"] = "campus_original"
        original, _ = run("S30", data, config)
        self.assertEqual(adapted["selected_candidate_evaluation"]["correct"], 8)
        self.assertEqual(original["selected_candidate_evaluation"]["correct"], 5)

    def test_s30_default_run_never_reads_missing_or_broken_final_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "student"
            lesson = root / "lesson-32"
            (lesson / "data").mkdir(parents=True)
            shutil.copytree(ROOT / "mlcourse", root / "mlcourse")
            for name in ("analysis.py", "config.json"):
                shutil.copy2(ROOT / "lesson-32" / name, lesson / name)
            shutil.copy2(ROOT / "lesson-32/data/base.json", lesson / "data/base.json")
            (lesson / "data/final.json").write_text("这不是 JSON", encoding="utf-8")

            first = subprocess.run(
                [sys.executable, str(lesson / "analysis.py")],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            first_summary = json.loads((lesson / "artifacts/summary.json").read_text(encoding="utf-8"))
            self.assertEqual(first_summary["evaluation_stage"], "development")

            (lesson / "data/final.json").unlink()
            shutil.rmtree(lesson / "artifacts")
            second = subprocess.run(
                [sys.executable, str(lesson / "analysis.py")],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            second_manifest = json.loads((lesson / "artifacts/manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn("--final-data", second_manifest["run_command"])
            self.assertNotIn("final_data_sha256", second_manifest)

    def test_s30_explicit_final_run_and_submission_are_separate(self):
        default_submission = json.loads((ROOT / "lesson-32/submission.json").read_text(encoding="utf-8"))
        final_submission = json.loads((ROOT / "lesson-32/submission-final.json").read_text(encoding="utf-8"))
        self.assertNotIn("--final-data", default_submission["run"])
        self.assertIn("--final-data", final_submission["run"])

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "final"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "lesson-32/analysis.py"),
                    "--data", str(ROOT / "lesson-32/data/base.json"),
                    "--final-data", str(ROOT / "lesson-32/data/final.json"),
                    "--config", str(ROOT / "lesson-32/config-final.json"),
                    "--output", str(output),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["evaluation_stage"], "final_evaluation")
            self.assertEqual(manifest["evaluation_stage"], "final_evaluation")
            self.assertIn("--final-data", manifest["run_command"])
            self.assertIn("final_data_sha256", manifest)

    def test_invalid_data_reports_problem_without_refreshing_old_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            output = base / "result"
            command = [
                sys.executable,
                str(ROOT / "lesson-27/analysis.py"),
                "--config",
                str(ROOT / "lesson-27/config-support.json"),
                "--output",
                str(output),
            ]
            first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(first.returncode, 0, first.stderr)
            before = (output / "summary.json").read_bytes()
            data = json.loads((ROOT / "lesson-27/data/base.json").read_text(encoding="utf-8"))
            data["project_id"] = "wrong-project"
            invalid = base / "invalid.json"
            invalid.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            failed = subprocess.run(
                [*command[:2], "--data", str(invalid), *command[2:]],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(failed.returncode, 2)
            self.assertIn("project_id", failed.stderr)
            self.assertIn("以前的输出没有更新", failed.stderr)
            self.assertEqual((output / "summary.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
