"""Validate the local 01–08 redesign on disposable copies, never on student work."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
STUDENT = ROOT / "course-student-template"
IDS = ["C01", "C02"] + [f"S{i:02d}" for i in range(1, 7)]
HEADINGS = ["本课要解决什么问题", "本课要学会什么", "课堂任务", "完成步骤", "必须提交什么", "不同起点怎么做", "运行限制"]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def command(root, args):
    started = time.monotonic()
    result = subprocess.run([sys.executable, *args], cwd=root, capture_output=True, text=True, timeout=90)
    require(result.returncode == 0, f"{' '.join(args)}\n{result.stdout}\n{result.stderr}")
    return {"command": [sys.executable, *args], "exit_code": result.returncode,
            "seconds": round(time.monotonic()-started, 4), "output": result.stdout.strip()}


def rows(path):
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def recompute(output):
    """Independent scalar arithmetic from emitted records; no model helper calls."""
    records = rows(output / "records.csv")
    groups = {}
    for row in records:
        if "prediction" not in row or "cnt" not in row:
            continue
        key = (row.get("split", "validation"), row.get("method", "selected"), row.get("seed", ""), row.get("budget_used", ""))
        groups.setdefault(key, []).append(row)
    result = []
    for key, group in groups.items():
        errors = [abs(float(row["prediction"])-float(row["cnt"])) for row in group]
        for row, error in zip(group, errors):
            column = "err_absolute" if "err_absolute" in row else "absolute_error"
            if column in row:
                require(abs(error-float(row[column])) < 1e-8, f"{output}: absolute error mismatch")
        result.append({"split_method_seed_budget": key, "n": len(group), "mae": sum(errors)/len(errors)})
    if (output / "comparison.csv").exists():
        for row in rows(output / "comparison.csv"):
            matches = [item for item in result if item["split_method_seed_budget"][:2] == (row["split"], row["method"])]
            require(len(matches) == 1, "comparison record identity mismatch")
            item = matches[0]
            require(int(row["n"]) == item["n"], "comparison denominator mismatch")
            require(abs(float(row["overall_mae"])-item["mae"]) < 1e-8, "comparison MAE mismatch")
        for row in rows(output / "group_metrics.csv"):
            if row["dimension"] != "commute" or row["group"] != "commute":
                continue
            selected = [record for record in records if record["split"] == row["split"] and record["method"] == row["method"]
                        and record["is_commute"].lower() in {"true", "1"}]
            require(len(selected) == int(row["n"]), "commute denominator mismatch")
            if selected:
                score = sum(abs(float(v["prediction"])-float(v["cnt"])) for v in selected)/len(selected)
                require(abs(score-float(row["mae"])) < 1e-8, "commute MAE mismatch")
    return result


def optional_reference_experiments(selected):
    reports = []
    with tempfile.TemporaryDirectory(prefix="ml-redesign-reference-") as temporary:
        scratch = Path(temporary) / "student"
        shutil.copytree(STUDENT, scratch, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "artifacts", ".venv"))
        for number in selected:
            directory = scratch / f"lesson-{number:02d}"
            executions = []
            if number < 8:
                sys.path.insert(0, str(scratch))
                from mlcourse import bike_course
                config = dict(bike_course.DEFAULTS[number])
                output = directory / "artifacts/author-reference"
                if number == 7:
                    config.update(stage="select", selection_note="作者可选参考：先登记条件与预算，再揭示已选训练标签。")
                    plan_output = directory / "artifacts/author-select"
                    selected_plan = bike_course.run_lesson(scratch, number, config)
                    bike_course._write_outputs(plan_output, selected_plan)
                    require("cnt" not in json.dumps(selected_plan["selection_plan.json"]), "selection plan must not reveal targets")
                    config.update(stage="reveal", selection_plan="artifacts/author-select/selection_plan.json")
                calculated = bike_course.run_lesson(scratch, number, config)
                bike_course._write_outputs(output, calculated)
                executions.append({"call": "optional bike_course.run_lesson", "lesson": number,
                                   "config": config, "scope": "teacher numerical reference; not the student's standard route"})
            else:
                cfg = "lesson-08/config-hour-onehot.json"
                prereg = "lesson-08/author-preregister.json"
                executions.append(command(scratch, ["scripts/lesson08.py", "preregister", "--config", cfg, "--output", prereg]))
                registered = read_json(scratch / prereg)
                registered.update(primary_metric="overall_mae", hypothesis="作者可选参考预计小时类别表示可以拟合非线性的小时峰形。",
                                  explanation="作者可选参考只替换小时表示，保持数据、算法和其他输入一致。",
                                  check_reason="作者可选参考预先以总体误差为主，另检查工作日时段组的代价。",
                                  check_rule={"minimum_primary_improvement": 0.0, "maximum_secondary_mae_increase": 10.0})
                save_json(scratch / prereg, registered)
                executions.append(command(scratch, ["scripts/lesson08.py", "bike", "--config", cfg, "--preregister", prereg,
                                                    "--output", "lesson-08/artifacts/author-reference"]))
                output = directory / "artifacts/author-reference"
            summary = read_json(output / "summary.json")
            if number != 4:
                require(summary.get("sealed_test_rows", 2168) == 2168, "sealed test count changed")
            if number == 4:
                audit = read_json(output / "audit.json")
                require(audit["rows"] == 17379 and audit["absent_timestamp_rows"] == 165, "calendar audit changed")
                require(len(rows(output / "missing_hours.csv")) == 165, "missing calendar rows mismatch")
            calculations = recompute(output)
            digest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}
            reports.append({"lesson": IDS[number-1], "number": number, "executions": executions,
                            "independent_record_recalculations": calculations, "result_sha256": digest,
                            "test_scores_opened": False, "scope": "author command and independent scalar arithmetic; not student trial"})
    return reports


def starter_entries(selected):
    reports = []
    with tempfile.TemporaryDirectory(prefix="ml-open-starter-") as temporary:
        scratch = Path(temporary) / "student"
        shutil.copytree(STUDENT, scratch, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "artifacts", ".venv"))
        for number in selected:
            if number == 8:
                args = ["lesson-08/analysis.py", "--output", "lesson-08/artifacts/author-starter"]
                output = scratch / "lesson-08/artifacts/author-starter"
            else:
                args = [f"lesson-{number:02d}/analysis.py", "--config", "config.json", "--output", "artifacts/author-starter"]
                output = scratch / f"lesson-{number:02d}/artifacts/author-starter"
            execution = command(scratch, args)
            require((output / "summary.json").exists(), "starter must produce a readable summary")
            reports.append({"lesson": IDS[number-1], "execution": execution,
                            "scope": "data/necessary baseline starter only; does not complete the open standard task",
                            "outputs": sorted(p.name for p in output.iterdir() if p.is_file())})
    return reports


def references(selected):
    return {"student_open_starters": starter_entries(selected),
            "teacher_optional_reference_experiments": optional_reference_experiments(selected),
            "standard_open_student_task_claimed_complete": False}


def documents():
    checks = []
    require({p.name for p in STUDENT.glob("lesson-*") if p.is_dir()} == {f"lesson-{i:02d}" for i in range(1, 9)}, "active student directories must be exactly 01–08")
    require({p.name for p in (ROOT / "course-instructor/lessons").iterdir() if p.is_dir()} == set(IDS), "active teacher directories mismatch")
    map_text = (ROOT / "machine-learning-course/COURSE_MAP.md").read_text()
    require(len(re.findall(r"^### \d\d", map_text, re.M)) == 32, "planning must contain all 32 lessons")
    for number, identifier in enumerate(IDS, 1):
        lesson = STUDENT / f"lesson-{number:02d}"
        for filename in ["README.md", "LEARN.md", "SUPPORT.md", "EXERCISES.md", "HINTS.md", "report.md", "analysis.py", "config.json", "contract.json", "submission.json"]:
            require((lesson / filename).is_file() and (lesson / filename).stat().st_size > 0, f"missing {lesson.name}/{filename}")
        actual = re.findall(r"^## (.+)$", (lesson / "README.md").read_text(), re.M)
        require(actual == HEADINGS, f"{lesson.name} seven README headings mismatch: {actual}")
        bank = read_json(ROOT / f"course-instructor/lessons/{identifier}/questions.json")
        require(bank["lesson_id"] == identifier, "question bank lesson ID mismatch")
        require(len(bank["concepts"]) == 5 and len(bank["questions"]) == 10, "bank must have five concepts and ten AB questions")
        pairs = {}
        for question in bank["questions"]:
            require(question["phase"] in {"A", "B"}, "question phase invalid")
            require(len(question["options"]) == 4 and len(set(question["options"])) == 4, "four distinct options required")
            require(type(question["answer"]) is int and 0 <= question["answer"] < 4, "unique indexed best answer required")
            require(question["explanation"].strip(), "question explanation required")
            pairs.setdefault(question["concept_id"], set()).add(question["phase"])
        require(len(pairs) == 5 and all(phases == {"A", "B"} for phases in pairs.values()), "AB pairs must examine same concept")
        checks.append({"number": number, "lesson": identifier, "complete_files": True, "bank_structure": True})
    broken = []
    for base in [STUDENT, ROOT / "course-instructor", ROOT / "machine-learning-course"]:
        for page in base.rglob("*.md"):
            if any(part in {"artifacts", "__pycache__", ".git"} for part in page.parts):
                continue
            for target in re.findall(r"\]\(([^)]+)\)", page.read_text(encoding="utf-8")):
                target = target.strip().strip("<>")
                if "://" in target or target.startswith(("#", "mailto:", "data:")):
                    continue
                target = target.split("#", 1)[0]
                if target and not (page.parent / target).exists():
                    broken.append(f"{page.relative_to(ROOT)} → {target}")
    require(not broken, "broken local links:\n" + "\n".join(broken[:80]))
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--references-only", action="store_true")
    parser.add_argument("--lesson", choices=IDS)
    parser.add_argument("--output", type=Path, default=ROOT / "validation/redesign.json")
    args = parser.parse_args()
    selected = [IDS.index(args.lesson)+1] if args.lesson else list(range(1, 9))
    report = {"python": sys.version, "scope": "local author verification; no publication or historical score mutation",
              "real_student_trial": False, "timings_are_execution_not_learning_time": True}
    try:
        if not args.references_only:
            report["documents_and_bank_structure"] = documents()
        report["references"] = references(selected)
        report["passed"] = True
    except (AssertionError, OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        report.update(passed=False, error=str(error))
    save_json(args.output, report)
    print(json.dumps({"passed": report["passed"], "report": str(args.output), "error": report.get("error")}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
