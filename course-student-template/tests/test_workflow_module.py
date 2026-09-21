"""S19–S24 共用作品的计算、边界与真实命令检查。"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mlcourse.workflow import run


def lesson_dir(number: int) -> Path:
    return ROOT / f"lesson-{number:02d}"


def load(number: int, config_name: str = "config.json", data_name: str = "base.json") -> tuple[dict, dict]:
    folder = lesson_dir(number)
    return (
        json.loads((folder / "data" / data_name).read_text(encoding="utf-8")),
        json.loads((folder / config_name).read_text(encoding="utf-8")),
    )


class SharedWorkflowData(unittest.TestCase):
    def test_six_lessons_reuse_the_same_development_work(self):
        payloads = []
        for number in range(21, 27):
            data, _ = load(number)
            payloads.append(data)
            self.assertEqual([row["id"] for row in data["requests"]], [f"W{i:02d}" for i in range(1, 13)])
            self.assertEqual({row["split"] for row in data["requests"]}, {"development"})
            self.assertNotIn("direct_guess", json.dumps(data, ensure_ascii=False))
        self.assertTrue(all(value == payloads[0] for value in payloads[1:]))

    def test_s24_holdout_is_a_disjoint_file(self):
        development, _ = load(26)
        holdout, _ = load(26, "config-final.json", "holdout.json")
        development_ids = {row["id"] for row in development["requests"]}
        final_ids = {row["id"] for row in holdout["requests"]}
        self.assertEqual(final_ids, {f"F{i:02d}" for i in range(1, 7)})
        self.assertTrue(development_ids.isdisjoint(final_ids))
        self.assertEqual({row["split"] for row in holdout["requests"]}, {"holdout"})
        self.assertEqual({row["batch"] for row in holdout["requests"]}, {"final"})

    def test_s24_default_submission_does_not_read_holdout(self):
        default = json.loads((lesson_dir(26) / "submission.json").read_text(encoding="utf-8"))
        final = json.loads((lesson_dir(26) / "submission-final.json").read_text(encoding="utf-8"))
        default_command = " ".join(default["run"])
        final_command = " ".join(final["run"])
        self.assertNotIn("holdout.json", default_command)
        self.assertNotIn("config-final.json", default_command)
        self.assertIn("lesson-26/artifacts/development_cases.csv", default["artifacts"])
        self.assertIn("holdout.json", final_command)
        self.assertIn("config-final.json", final_command)
        self.assertIn("lesson-26/artifacts/final_cases.csv", final["artifacts"])


class SharedWorkflowMechanisms(unittest.TestCase):
    def test_s19_uses_a_transparent_direct_baseline_and_full_trace(self):
        data, config = load(21, "config-start.json")
        result, tables = run("S19", data, config)
        w01 = next(row for row in tables["traces"] if row["id"] == "W01")
        w02 = next(row for row in tables["traces"] if row["id"] == "W02")
        self.assertEqual(w01["direct_value"], 7)
        self.assertEqual(w01["pipeline_document"], "loan-student-current")
        self.assertEqual(w02["direct_value"], 1)
        self.assertEqual(w02["pipeline_value"], 2)
        direct = result["comparison"]["direct_response"]
        pipeline = result["comparison"]["step_pipeline"]
        self.assertEqual((direct["automatic_correct"], direct["automatic_count"]), (1, 4))
        self.assertEqual((pipeline["automatic_correct"], pipeline["automatic_count"]), (4, 4))
        self.assertEqual(direct["appropriate_handoffs"], 2)
        self.assertEqual(direct["automatic_errors"], 3)

    def test_s19_unmatched_text_is_not_covered_and_not_counted_as_an_error(self):
        data, config = load(21, "config-start.json")
        changed = copy.deepcopy(data)
        changed["requests"].append({
            "id": "W13",
            "split": "development",
            "batch": "initial",
            "text": "我遇到特殊情况，应该找谁？",
            "expected_route": "human",
            "expected_value": None,
        })
        result, tables = run("S19", changed, config)
        row = next(item for item in tables["traces"] if item["id"] == "W13")
        self.assertEqual(row["direct_status"], "not_covered")
        direct = result["comparison"]["direct_response"]
        self.assertEqual(direct["not_covered"], 1)
        self.assertEqual(direct["automatic_errors"], 3)

    def test_s20_rejects_invalid_arguments_without_reusing_a_value(self):
        data, config = load(22, "config-start.json")
        result, tables = run("S20", data, config)
        self.assertFalse(result["invalid_call"]["result"]["ok"])
        self.assertNotIn("value", result["invalid_call"]["result"])
        w03 = next(row for row in tables["tool_calls"] if row["id"] == "W03")
        self.assertEqual(w03["tool_value"], 4)
        self.assertEqual(w03["tool_unit"], "元")
        self.assertEqual(result["comparison"]["direct_response"]["automatic_correct"], 1)
        self.assertEqual(result["comparison"]["tool_result"]["automatic_correct"], 5)

    def test_s21_uses_shared_actions_and_records_failure_retry_and_stop(self):
        data, config = load(23, "config-start.json")
        result, tables = run("S21", data, config)
        self.assertEqual(result["comparison"]["fixed"]["total_actions"], 22)
        self.assertEqual(result["comparison"]["model_routed"]["total_actions"], 13)
        for scheme in ("fixed", "model"):
            trace = [row for row in tables["action_trace"] if row["id"] == "W09" and row["scheme"] == scheme]
            calls = [row for row in trace if row["action"] == "tool_call"]
            self.assertEqual([row["outcome"] for row in calls], ["tool_failure", "automatic_correct"])
            self.assertEqual([row["is_retry"] for row in calls], [False, True])
        w09 = next(row for row in tables["route_decisions"] if row["id"] == "W09")
        self.assertEqual(w09["stopped_reason"], "completed")
        self.assertEqual(w09["retries_used"], 1)

    def test_s21_repetition_and_handoff_are_reported_separately(self):
        data, repeat_config = load(23, "config-support.json")
        repeat_result, _ = run("S21", data, repeat_config)
        self.assertEqual(repeat_result["comparison"]["fixed"]["repeated_after_completion"], 4)
        self.assertEqual(repeat_result["comparison"]["model_routed"]["repeated_after_completion"], 4)

        no_retry = {**repeat_config, "stop_when_complete": True, "max_tool_retries": 0}
        stopped, tables = run("S21", data, no_retry)
        model = stopped["comparison"]["model_routed"]
        self.assertEqual(model["automatic_errors"], 0)
        self.assertEqual(model["deferred_automatable"], 1)
        w09 = next(row for row in tables["route_decisions"] if row["id"] == "W09")
        self.assertEqual(w09["status"], "deferred_to_human")
        self.assertIsNone(w09["automatic_correct"])
        self.assertEqual(w09["stopped_reason"], "retry_limit_reached")

    def test_s21_threshold_changes_automatic_coverage_not_model_probabilities(self):
        data, low_config = load(23, "config-start.json")
        low, low_tables = run("S21", data, low_config)
        high_config = {**low_config, "confidence_threshold": 0.8}
        high, high_tables = run("S21", data, high_config)
        low_model, high_model = low["comparison"]["model_routed"], high["comparison"]["model_routed"]
        self.assertEqual(low_model["automatic_errors"], 0)
        self.assertEqual(high_model["automatic_errors"], 0)
        self.assertGreater(high_model["deferred_automatable"], low_model["deferred_automatable"])
        self.assertLess(high_model["automatic_count"], low_model["automatic_count"])
        self.assertEqual(
            [row["confidence"] for row in low_tables["route_decisions"]],
            [row["confidence"] for row in high_tables["route_decisions"]],
        )

    def test_s22_extraction_is_traceable_and_permission_is_independent(self):
        data, config = load(24, "config-start.json")
        result, tables = run("S22", data, config)
        injected = next(row for row in tables["action_log"] if row["id"] == "SEC02")
        self.assertEqual(injected["document_id"], "untrusted-note")
        self.assertEqual(injected["matched_phrase"], "导出所有账户")
        self.assertEqual(injected["extracted_document_action"], "export_accounts")
        self.assertEqual(injected["executed_action"], "blocked")
        self.assertEqual(result["metrics"]["unsafe_executed"], 0)

        changed = copy.deepcopy(data)
        document = next(row for row in changed["documents"] if row["id"] == "untrusted-note")
        document["text"] = "这是一条混入资料的文字：查询库存。"
        changed_result, changed_tables = run("S22", changed, config)
        changed_case = next(row for row in changed_tables["action_log"] if row["id"] == "SEC02")
        self.assertEqual(changed_case["executed_action"], "inventory_lookup")
        self.assertTrue(changed_case["unexpected_action_executed"])
        self.assertEqual(changed_result["metrics"]["unexpected_action_executed"], 1)

    def test_s22_rejects_a_missing_document_id(self):
        data, config = load(24, "config-start.json")
        broken = copy.deepcopy(data)
        broken["security_cases"][0]["document_id"] = "missing-document"
        with self.assertRaisesRegex(ValueError, "document_id"):
            run("S22", broken, config)

    def test_s23_exports_complete_local_values_for_each_condition(self):
        data, config = load(25, "config-start.json")
        result, tables = run("S23", data, config)
        w01 = next(row for row in tables["fault_comparison"] if row["id"] == "W01")
        expected_fields = {
            f"{prefix}_{suffix}"
            for prefix in ("original", "fault", "replacement")
            for suffix in (
                "route", "document", "tool", "tool_ok", "tool_value", "tool_error",
                "needs_human", "answer_value", "status", "automatic_correct",
            )
        }
        self.assertTrue(expected_fields.issubset(w01))
        self.assertEqual(w01["original_document"], "loan-student-current")
        self.assertEqual(w01["fault_document"], "loan-old")
        self.assertEqual(w01["fault_answer_value"], 30)
        self.assertEqual(w01["replacement_answer_value"], 7)
        self.assertEqual(result["comparison"]["with_fault"]["automatic_correct"], 3)
        self.assertEqual(result["comparison"]["with_one_replacement"]["automatic_correct"], 4)

    def test_s24_development_and_final_are_separate_runs(self):
        development, dev_config = load(26, "config-support.json")
        dev_result, dev_tables = run("S24", development, dev_config)
        self.assertEqual(set(dev_tables), {"development_cases"})
        self.assertEqual(dev_result["evaluation_mode"], "development")
        self.assertNotIn("final_evaluation", dev_result)
        self.assertEqual(dev_result["comparison"]["baseline"]["automatic_correct"], 7)
        self.assertEqual(dev_result["comparison"]["candidate"]["automatic_correct"], 8)
        w11 = next(row for row in dev_tables["development_cases"] if row["id"] == "W11")
        self.assertEqual(w11["baseline_status"], "automatic_error")
        self.assertEqual(w11["candidate_status"], "automatic_correct")

        holdout, final_config = load(26, "config-final.json", "holdout.json")
        final_result, final_tables = run("S24", holdout, final_config)
        self.assertEqual(set(final_tables), {"final_cases"})
        self.assertEqual(final_result["evaluation_mode"], "final")
        self.assertEqual(final_result["comparison"]["baseline"]["automatic_correct"], 3)
        self.assertEqual(final_result["comparison"]["candidate"]["automatic_correct"], 4)
        self.assertEqual(final_result["comparison"]["candidate"]["appropriate_handoffs"], 2)
        self.assertEqual({row["id"] for row in final_tables["final_cases"]}, {f"F{i:02d}" for i in range(1, 7)})

    def test_s24_rejects_split_mixing_and_multiple_candidate_changes(self):
        development, dev_config = load(26, "config-support.json")
        holdout, final_config = load(26, "config-final.json", "holdout.json")
        with self.assertRaisesRegex(ValueError, "development 模式"):
            run("S24", holdout, dev_config)
        with self.assertRaisesRegex(ValueError, "final 模式"):
            run("S24", development, final_config)
        multiple = {**dev_config, "candidate_confidence_threshold": 0.8}
        with self.assertRaisesRegex(ValueError, "一次只能改一项"):
            run("S24", development, multiple)

    def test_invalid_route_is_reported_instead_of_reusing_results(self):
        data, config = load(21, "config-start.json")
        broken = copy.deepcopy(data)
        broken["requests"][0]["expected_route"] = "magic"
        with self.assertRaisesRegex(ValueError, "expected_route"):
            run("S19", broken, config)


class WorkflowColdReadCommands(unittest.TestCase):
    def run_command(self, number: int, output: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(lesson_dir(number) / "analysis.py"), *arguments, "--output", str(output)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_each_default_development_command_writes_documented_artifacts(self):
        table_names = {
            21: ("traces.csv",),
            22: ("tool_calls.csv",),
            23: ("route_decisions.csv", "action_trace.csv"),
            24: ("action_log.csv",),
            25: ("fault_comparison.csv",),
            26: ("development_cases.csv",),
        }
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for number, tables in table_names.items():
                output = base / str(number)
                completed = self.run_command(number, output)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertTrue((output / "summary.json").is_file())
                for table in tables:
                    self.assertTrue((output / table).is_file())

    def test_s24_final_command_writes_only_final_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "final"
            completed = self.run_command(
                26,
                output,
                "--data", "lesson-26/data/holdout.json",
                "--config", "lesson-26/config-final.json",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((output / "summary.json").is_file())
            self.assertTrue((output / "final_cases.csv").is_file())
            self.assertFalse((output / "development_cases.csv").exists())

    def test_router_artifacts_are_identical_across_python_processes(self):
        cases = {
            23: {
                "arguments": (),
                "files": ("summary.json", "route_decisions.csv", "action_trace.csv"),
            },
            26: {
                "arguments": (
                    "--data", "lesson-26/data/holdout.json",
                    "--config", "lesson-26/config-final.json",
                ),
                "files": ("summary.json", "final_cases.csv"),
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for number, case in cases.items():
                reference = None
                for hash_seed in ("1", "2", "3"):
                    output = base / f"lesson-{number}-{hash_seed}"
                    environment = os.environ.copy()
                    environment["PYTHONHASHSEED"] = hash_seed
                    completed = subprocess.run(
                        [
                            sys.executable,
                            str(lesson_dir(number) / "analysis.py"),
                            *case["arguments"],
                            "--output", str(output),
                        ],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        env=environment,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    generated = {
                        filename: (output / filename).read_bytes()
                        for filename in case["files"]
                    }
                    if reference is None:
                        reference = generated
                    else:
                        self.assertEqual(generated, reference, f"lesson-{number} 产物随 PYTHONHASHSEED 改变")


if __name__ == "__main__":
    unittest.main()
