"""Focused runtime and evidence checks for the S07-S12 candidate package."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class S07S12Candidate(unittest.TestCase):
    def run_lesson(self, number: int, config: str = "config.json") -> Path:
        temporary = tempfile.TemporaryDirectory(prefix=f"lesson-{number:02d}-")
        self.addCleanup(temporary.cleanup)
        output = Path(temporary.name) / "output"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / f"lesson-{number:02d}/analysis.py"),
                "--config",
                str(ROOT / f"lesson-{number:02d}/{config}"),
                "--output",
                str(output),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return output

    def test_s07_validation_run_does_not_reveal_test_results(self):
        output = self.run_lesson(9, "config-start.json")
        rows = read_csv(output / "comparison.csv")
        self.assertEqual({row["evaluation_split"] for row in rows}, {"validation"})
        self.assertNotIn("test_mae_minutes", rows[0])
        records = read_csv(output / "records.csv")
        self.assertEqual({row["split"] for row in records}, {"validation"})

    def test_s08_metrics_match_selected_records(self):
        output = self.run_lesson(10, "config-start.json")
        policies = {row["policy"]: row for row in read_csv(output / "comparison.csv")}
        records = read_csv(output / "records.csv")
        selected = [row for row in records if row["original_selected"] == "True"]
        true_positive = sum(row["actual_needs_review"] == "1" for row in selected)
        self.assertEqual(int(policies["original_threshold"]["selected_count"]), len(selected))
        self.assertAlmostEqual(float(policies["original_threshold"]["precision"]), true_positive / len(selected), places=6)

    def test_s09_challenge_cases_are_traceable_in_both_representations(self):
        output = self.run_lesson(11, "config-support.json")
        rows = read_csv(output / "challenge.csv")
        self.assertEqual({row["id"] for row in rows}, {"P01", "P02", "P03"})
        self.assertEqual({row["representation"] for row in rows}, {"raw", "prepared"})
        self.assertTrue(all(row["nearest_ids"] for row in rows))

    def test_s10_first_update_uses_reported_gradient(self):
        output = self.run_lesson(12, "config-start.json")
        rows = read_csv(output / "first_update.csv")
        row = next(item for item in rows if item["parameter"] == "message_length")
        expected = float(row["before"]) - 0.15 * float(row["gradient"])
        self.assertAlmostEqual(float(row["after"]), expected, places=7)

    def test_s11_separates_source_and_target_counts(self):
        output = self.run_lesson(13, "config-start.json")
        summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["source_unlabeled_count"], 60)
        self.assertEqual(summary["target_train_count"], 24)
        self.assertIn("冻结", summary["note"])
        self.assertIn("不是大型预训练模型", summary["note"])

    def test_s12_more_epochs_separates_train_and_validation(self):
        output = self.run_lesson(14, "config-start.json")
        rows = {row["method"]: row for row in read_csv(output / "comparison.csv")}
        self.assertLess(float(rows["candidate"]["train_log_loss"]), float(rows["starting"]["train_log_loss"]))
        self.assertGreater(float(rows["candidate"]["evaluation_log_loss"]), float(rows["starting"]["evaluation_log_loss"]))


if __name__ == "__main__":
    unittest.main()
