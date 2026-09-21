"""教师独立核对 S25–S30 的关键分母与结论边界。"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

INSTRUCTOR = Path(__file__).resolve().parents[1]
STUDENT = INSTRUCTOR.parent / "course-student-template"
sys.path.insert(0, str(STUDENT))

from mlcourse.operations import run


def load(number: int) -> tuple[dict, dict]:
    folder = STUDENT / f"lesson-{number:02d}"
    data = json.loads((folder / "data/base.json").read_text(encoding="utf-8"))
    if number == 32:
        final = json.loads((folder / "data/final.json").read_text(encoding="utf-8"))
        data.update({key: value for key, value in final.items() if key not in {"kind", "project_id", "source"}})
    config = json.loads((folder / "config-support.json").read_text(encoding="utf-8"))
    return data, config


class OperationsReferenceChecks(unittest.TestCase):
    def test_feedback_denominators_are_conserved(self):
        data, config = load(27)
        result, tables = run("S25", data, config)
        expected_rows = 2 * len(config["seeds"]) * len(data["feedback_rounds"])
        self.assertEqual(len(tables["rounds"]), expected_rows)
        for row in tables["episodes"]:
            self.assertEqual(sum(row["action_counts"].values()), 16)
        self.assertEqual(result["comparison"]["greedy"]["mean_feedback_per_round"], 0.5)

    def test_delayed_scores_recompute_from_trajectory(self):
        data, config = load(28)
        result, tables = run("S26", data, config)
        totals = {policy: 0.0 for policy in ("fast_auto", "risk_aware")}
        for row in tables["trajectories"]:
            totals[row["policy"]] += row["long_term_score"]
        self.assertEqual(totals, result["comparison"]["long_term_score"]["scores"])

    def test_monitoring_never_counts_missing_labels(self):
        data, config = load(29)
        result, _ = run("S27", data, config)
        current = result["batches"]["current"]
        self.assertEqual(current["known_accuracy"], current["known_correct"] / current["labeled_n"])
        self.assertEqual(current["labeled_n"] + current["unlabeled_n"], current["n"])

    def test_cache_counts_and_costs_recompute(self):
        data, config = load(30)
        result, _ = run("S28", data, config)
        for row in result["deterministic_comparison"]:
            self.assertEqual(row["fresh_calls"] + row["cache_hits"], row["n"])
            unit = config["estimated_cost_per_fresh_call"][row["profile"]]
            self.assertEqual(row["estimated_cost_units"], row["fresh_calls"] * unit)

        personal = json.loads((STUDENT / "lesson-30/config-check.json").read_text(encoding="utf-8"))
        changed, tables = run("S28", data, personal)
        rows = {
            (row["profile"], row["cache_enabled"]): row
            for row in changed["repeat_input_check"]["comparison_after_change"]
        }
        self.assertEqual(rows[("fast", True)]["cache_hits"], 1)
        self.assertTrue(all("request_latency_ms" not in row for row in tables["records"]))
        self.assertTrue(all("request_latency_ms" not in row for row in tables["changed_records"]))

    def test_transfer_and_final_use_equal_denominators(self):
        for number, lesson, key in ((31, "S29", "comparison"), (32, "S30", "final_evaluation")):
            data, config = load(number)
            result, _ = run(lesson, data, config)
            self.assertEqual(result[key]["original"]["n"], result[key]["adapted"]["n"])

    def test_student_transfer_check_preserves_the_provided_eight_row_result(self):
        data, _ = load(31)
        config = json.loads((STUDENT / "lesson-31/config.json").read_text(encoding="utf-8"))
        result, tables = run("S29", data, config)
        self.assertEqual(result["provided_comparison"]["original"], {"correct": 6, "n": 8})
        self.assertEqual(result["provided_comparison"]["adapted"], {"correct": 8, "n": 8})
        self.assertEqual(result["comparison"]["original"]["n"], 9)
        self.assertEqual(len(tables["transfer_records"]), 9)

    def test_release_candidate_is_fixed_before_final_evaluation(self):
        data, config = load(32)
        adapted, _ = run("S30", data, config)
        config["release_candidate"] = "campus_original"
        original, _ = run("S30", data, config)
        self.assertEqual(adapted["selected_candidate_evaluation"], {"scheme": "adapted", "correct": 8, "n": 8})
        self.assertEqual(original["selected_candidate_evaluation"], {"scheme": "original", "correct": 5, "n": 8})


if __name__ == "__main__":
    unittest.main()
