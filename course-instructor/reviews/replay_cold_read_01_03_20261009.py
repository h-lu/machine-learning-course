"""Replay a simulated student's own 01–03 work in a fresh disposable copy.

Run from the course workspace root. This teacher-only evidence does not modify
the student template, install software, or turn simulation into human trial data.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIXTURE = HERE / "COLD_READ_01_03_20261009.json"


def independent_arithmetic(student: Path, expected: dict) -> dict:
    """Use raw CSV and stdlib arithmetic, not the student's shared functions."""
    train, validation = [], []
    with (student / "data/bike/hour.csv").open(newline="") as stream:
        for raw in csv.DictReader(stream):
            if raw["dteday"] >= "2012-10-01":
                continue  # No sealed target is parsed or evaluated.
            row = {"hr": int(raw["hr"]), "temp": float(raw["temp"]),
                   "cnt": int(raw["cnt"])}
            (train if raw["dteday"] < "2012-07-01" else validation).append(row)
    assert (len(train), len(validation)) == (13003, 2208)

    def average(values):
        return math.fsum(values) / len(values)

    def error(predict):
        return average([abs(predict(row) - row["cnt"]) for row in validation])

    mean = average([row["cnt"] for row in train])
    xbar = average([row["temp"] for row in train])
    slope = math.fsum((row["temp"] - xbar) * (row["cnt"] - mean) for row in train)
    slope /= math.fsum((row["temp"] - xbar) ** 2 for row in train)
    intercept = mean - slope * xbar
    hour_means = {hour: average([row["cnt"] for row in train if row["hr"] == hour])
                  for hour in range(24)}
    values = {"mean": mean, "intercept": intercept, "slope": slope,
              "mae_manual": error(lambda row: 40 + 300 * row["temp"]),
              "mae_alternative": error(lambda row: 40 + 450 * row["temp"]),
              "mae_mean": error(lambda row: mean),
              "mae_line": error(lambda row: max(0, intercept + slope * row["temp"])),
              "mae_hour_mean": error(lambda row: hour_means[row["hr"]])}
    for key, value in values.items():
        assert math.isclose(value, expected[key], rel_tol=1e-10, abs_tol=1e-10), key
    summary = json.loads((student / "lesson-03/artifacts/personal/summary.json").read_text())
    for observed in summary["counts"]:
        counts = dict.fromkeys(["hit", "false_alert", "miss", "correct_no_alert"], 0)
        for row in validation:
            alert, high = hour_means[row["hr"]] >= observed["threshold"], row["cnt"] >= 500
            outcome = ("hit" if high else "false_alert") if alert else (
                "miss" if high else "correct_no_alert")
            counts[outcome] += 1
        assert all(counts[key] == observed[key] for key in counts)
    return values


def main() -> None:
    fixture = json.loads(FIXTURE.read_text())
    results = []
    with tempfile.TemporaryDirectory(prefix="ml-student-coldread-") as temp:
        student = Path(temp) / "student"
        shutil.copytree(ROOT / "course-student-template", student,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", "artifacts"))

        def execute(arguments: list[str], expected_code: int = 0) -> None:
            process = subprocess.run([sys.executable, *arguments], cwd=student,
                                     capture_output=True, text=True, timeout=600)
            if process.returncode != expected_code:
                raise AssertionError(f"Unexpected exit for relative command: {arguments}")
            results.append({"command": ["python3", *arguments],
                            "exit_code": process.returncode, "expected": expected_code})

        for number in (1, 2, 3):
            lesson = f"lesson-{number:02d}"
            execute([f"{lesson}/analysis.py"])
            summary = json.loads((student / lesson / "artifacts/starter/summary.json").read_text())
            assert summary["status"] == "not_started" and summary["prepared"]
            names = {p.name for p in (student / lesson / "artifacts/starter").iterdir()}
            expected_names = {"audit.json", "summary.json", "config_snapshot.json", "sample.csv"}
            if number == 2:
                expected_names.add("baseline.json")
            assert names == expected_names
            execute(["scripts/course.py", "check", f"{number:02d}"], expected_code=1)

        for relative, text in fixture["student_files"].items():
            path = student / relative
            assert not Path(relative).is_absolute() and path.resolve().is_relative_to(student)
            path.write_text(text)
        for number in (1, 2, 3):
            execute(["scripts/course.py", "run", f"{number:02d}"])
            execute(["scripts/course.py", "check", f"{number:02d}"])
        execute(["scripts/course.py", "ci"])
        metrics = independent_arithmetic(student, fixture["independent_arithmetic"])
        digests = {relative: hashlib.sha256((student / relative).read_bytes()).hexdigest()
                   for relative in fixture["submitted_artifact_sha256"]}
        print(json.dumps({"command_results": results, "ci_byte_reproduction": "passed",
                          "independent_arithmetic": "passed", "metrics": metrics,
                          "test_targets_evaluated": False,
                          "matches_recorded_artifact_bytes": digests == fixture["submitted_artifact_sha256"],
                          "human_90_minute_pilot": False}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
