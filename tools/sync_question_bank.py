"""Build the reviewed local bank, not the 32-lesson deployment bank.

No student files are written. Preserve the production bank's other lessons when
preparing a deployment; lesson10's pinned full bank is under ml-check/deploy/banks.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml-check"))
from ml_check.checker import active_ids, formal_question_numbers, Report, check_question_set, read_json


def main():
    lessons = []
    report = Report(ROOT / "course-instructor", "instructor")
    ids = active_ids(ROOT / "course-instructor", "instructor")
    numbers = formal_question_numbers(ROOT / "course-instructor", ids)
    for id in ids:
        path = ROOT / "course-instructor/lessons" / id / "questions.json"
        value = read_json(path, report)
        check_question_set(value, path, report, id, numbers.get(id))
        if not isinstance(value, dict):
            continue
        if id.startswith("C"):
            module = "开始一个项目"
        else:
            module = [
                "问题与评价",
                "学习、表示与泛化",
                "预训练模型复用",
                "模型、工具与人的协作",
                "反馈、使用与迁移",
            ][((int(id[1:]) - 1) // 6)]
        lessons.append({**value, "module": module})
    if report.failed(True):
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
        return 1
    target = ROOT / "ml-check/app/question_bank/lessons.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"version": "ml-lesson10-sms-20261013-v1", "lessons": lessons}, ensure_ascii=False, indent=2) + "\n")
    print(f"已汇集 {len(lessons)} 课、{sum(len(x['questions']) for x in lessons)} 题。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
