"""Build the versioned teacher-side bank. No student files are written."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml-check"))
from ml_check.checker import LESSONS, Report, check_question_set, read_json


def main():
    lessons = []
    report = Report(ROOT / "course-instructor", "instructor")
    for id in LESSONS:
        path = ROOT / "course-instructor/lessons" / id / "questions.json"
        value = read_json(path, report)
        check_question_set(value, path, report, id)
        if not isinstance(value, dict):
            continue
        if id.startswith("C"):
            module = "开始一个项目"
        else:
            module = ["问题与评价", "经典学习", "深度学习与注意力", "语言模型与应用", "连续决策与使用"][((int(id[1:]) - 1) // 6)]
        lessons.append({**value, "module": module})
    if report.failed(True):
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
        return 1
    target = ROOT / "ml-check/app/question_bank/lessons.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"version": "ml-v10-s01-review-2026-09-19", "lessons": lessons}, ensure_ascii=False, indent=2) + "\n")
    print(f"已汇集 {len(lessons)} 课、{sum(len(x['questions']) for x in lessons)} 题。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
