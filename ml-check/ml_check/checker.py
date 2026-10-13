"""Check material structure without running submitted commands or judging choices."""
from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

LESSONS = ["C01", "C02"] + [f"S{i:02d}" for i in range(1, 31)]
HEADINGS = ["本课要解决什么问题", "本课要学会什么", "课堂任务", "完成步骤",
            "必须提交什么", "不同起点怎么做", "运行限制"]
TASK_FIELDS = ["question", "user", "data_source", "metric", "split_plan", "initial_expectation"]


def active_ids(root: Path, profile: str) -> list[str]:
    """Keep the 32-lesson plan separate from currently available packages."""
    path = root / "active_lessons.json"
    if not path.is_file():
        return [f"lesson-{i:02d}" for i in range(1, 33)] if profile == "student" else LESSONS
    value = json.loads(path.read_text(encoding="utf-8"))
    key = "active_student_lessons" if profile == "student" else "active_instructor_lessons"
    ids = value[key]
    allowed = [f"lesson-{i:02d}" for i in range(1, 33)] if profile == "student" else LESSONS
    if not isinstance(ids, list) or not ids or ids != [item for item in allowed if item in ids]:
        raise ValueError("活跃课次清单必须按完整课程顺序列出不重复的合法编号")
    return ids
# Scan current student prose, not archives, field names or historical explanations.
OLD_TERMS = ["问题契约", "知识自查", "使用决定", "输入契约", "指标契约", "MDP 契约",
             "知识自查", "门禁", "签收", "消费测试集", "运行前预测", "样本单位", "预测时点",
             "适用边界", "委托", "红组", "蓝组", "负责决定", "适用范围",
             "锁定", "行动规则", "回退/撤回"]


@dataclass
class Report:
    root: Path
    profile: str
    issues: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def add(self, path: Path, code: str, message: str, severity: str = "error") -> None:
        try:
            name = str(path.relative_to(self.root))
        except ValueError:
            name = str(path)
        self.issues.append(dict(path=name, code=code, message=message, severity=severity))

    def as_dict(self) -> dict:
        result = asdict(self)
        result["root"] = str(self.root)
        return result

    def failed(self, strict: bool = False) -> bool:
        return any(x["severity"] == "error" or strict for x in self.issues)


def read_json(path: Path, report: Report):
    try:
        def invalid(value):
            raise ValueError(f"非有限数值 {value}")
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=invalid)
    except (OSError, UnicodeError, ValueError) as exc:
        report.add(path, "json", f"无法读取有效 JSON：{exc}")
        return None


def required(path: Path, report: Report) -> bool:
    if not path.is_file():
        report.add(path, "missing", "缺少文件，请补齐或修正引用路径。")
        return False
    return True


def local_path(value, report: Report, source: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        report.add(source, "path", "结果与报告路径应为仓库内非空相对路径。")
        return None
    p = Path(value)
    if p.is_absolute() or not (report.root / p).resolve().is_relative_to(report.root.resolve()):
        report.add(source, "path", "结果与报告路径必须位于当前仓库内。")
        return None
    return report.root / p


def check_prose(path: Path, report: Report, student: bool = False) -> None:
    text = path.read_text(encoding="utf-8")
    if student:
        allowed_terms = set()
        # Literal approved lesson10 terminology, without relaxing other lessons.
        relative = path.relative_to(report.root)
        if report.profile == "student" and relative.parts[0] == "lesson-10":
            if all(word in text for word in ("概率", "阈值", "容量")):
                allowed_terms.add("行动规则")
            if path.name == "README.md" and all(word in text for word in ("历史英语短信", "当前中文短信")):
                allowed_terms.add("适用范围")
        for word in set(OLD_TERMS):
            if word in text and word not in allowed_terms:
                report.add(path, "wording", f"请用具体动作或解释替换旧说法：{word}")
        if re.search(r"\b(?:Core|Support|Upgrade|Transfer|Open extension)\b", text):
            # Headings may contain English only after the Chinese explanation.
            for line in text.splitlines():
                if re.match(r"^#{1,6}\s+(?:Core|Support|Upgrade|Transfer|Open extension)\b", line):
                    report.add(path, "wording", "分层标题先写中文名称并说明要做什么。")
    # File links are checked where they are written, including links to sibling repos.
    for match in re.finditer(r"(?<!!)\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", text):
        target = match.group(1).strip("<>").split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        if not (path.parent / target).exists():
            report.add(path, "link", f"链接目标不存在：{target}")


def check_submission(folder: Path, report: Report) -> None:
    task_path, sub_path = folder / "contract.json", folder / "submission.json"
    task, sub = read_json(task_path, report), read_json(sub_path, report)
    if not isinstance(task, dict) or not isinstance(sub, dict):
        report.add(folder, "schema", "任务说明与提交清单应为 JSON 对象。")
        return
    # V2 student templates use numeric lesson-* directories and the `lesson`
    # field; accept legacy C/S directories and lesson_id for existing clones.
    expected = folder.name
    for obj, path in [(task, task_path), (sub, sub_path)]:
        value = obj.get("lesson", obj.get("lesson_id"))
        if value != expected:
            report.add(path, "lesson", "课次编号应与目录相同。")
    for key in TASK_FIELDS:
        if not isinstance(task.get(key), str):
            report.add(task_path, "task", f"任务说明需要文字字段 {key}。")
    status = sub.get("status")
    if status not in ("template", "not_started", "in_progress", "complete"):
        report.add(sub_path, "status", "状态应为 not_started、in_progress 或 complete。")
    run = sub.get("run")
    if not ((isinstance(run, str) and run.strip()) or (isinstance(run, list) and run and all(isinstance(x, str) and x for x in run))):
        report.add(sub_path, "run", "请填写从仓库根目录运行项目的命令。工具不会执行这条命令。")
    report_file = local_path(sub.get("report"), report, sub_path)
    if report_file is not None:
        required(report_file, report)
    artifacts = sub.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        report.add(sub_path, "artifacts", "请列出至少一个程序生成结果的相对路径。")
        artifacts = []
    for item in artifacts:
        p = local_path(item, report, sub_path)
        if p is not None and status == "complete":
            required(p, report)
    if status == "complete":
        for key in TASK_FIELDS:
            if not isinstance(task.get(key), str) or not task[key].strip():
                report.add(task_path, "incomplete", f"已完成的项目需要说明 {key}，可引用报告段落。")
        if report_file is not None and report_file.is_file():
            content = report_file.read_text(encoding="utf-8")
            if "完成实验后，用实际数据说明：" in content:
                report.add(report_file, "incomplete", "报告仍是入门提示，请写入自己的实验与判断。")
    report.stats[status or "unknown"] = report.stats.get(status or "unknown", 0) + 1


def check_question_set(value, path: Path, report: Report, lesson_id: str, concept_numbers: list[int] | None = None) -> None:
    if not isinstance(value, dict) or value.get("lesson_id") != lesson_id:
        report.add(path, "questions", "题目课次与目录不一致。")
        return
    numbers = list(range(1, 6)) if concept_numbers is None else concept_numbers
    if not isinstance(numbers, list) or len(numbers) != 5 or any(type(n) is not int or not 1 <= n <= 99 for n in numbers) or numbers != sorted(set(numbers)):
        report.add(path, "concepts", "离线草稿须明确五个按顺序排列且不重复的两位题号。")
        return
    concepts = value.get("concepts")
    expected_concept_ids = [f"{lesson_id}-{index:02d}" for index in numbers]
    if not isinstance(concepts, list) or len(concepts) != 5:
        report.add(path, "concepts", "每课需要独立定义五个知识点，供 A、AI 学习和 B 三阶段共同使用。")
        concepts = []
    concept_ids = []
    for index, concept in enumerate(concepts, 1):
        if not isinstance(concept, dict):
            report.add(path, "concepts", "每个知识点应为对象。")
            continue
        concept_id = concept.get("concept_id")
        concept_ids.append(concept_id)
        if concept_id != expected_concept_ids[index - 1]:
            report.add(path, "concepts", "知识点编号须与本课明确登记的题号一致。")
        for key in ("title", "tutor_context"):
            if not isinstance(concept.get(key), str) or not concept[key].strip():
                report.add(path, "concepts", f"知识点缺少非空字段 {key}。")
        title = str(concept.get("title", ""))
        if re.fullmatch(r"(?:知识点|概念)\s*\d+", title):
            report.add(path, "concepts", "知识点标题必须写出具体内容，不能使用“概念 1”之类占位名。")
    if concept_ids and concept_ids != expected_concept_ids:
        report.add(path, "concepts", "五个知识点必须按编号顺序排列且不能重复。")

    questions = value.get("questions")
    if not isinstance(questions, list) or len(questions) != 10:
        report.add(path, "questions", "每课需要 A、B 各五道概念题。")
        return
    seen, phases, question_concepts = set(), [], []
    for q in questions:
        if not isinstance(q, dict):
            report.add(path, "questions", "每道题应为对象。")
            continue
        qid = q.get("id")
        if not isinstance(qid, str) or qid in seen:
            report.add(path, "questions", "题目编号应为互不重复的文字。")
        if isinstance(qid, str):
            seen.add(qid)
        phases.append(q.get("phase"))
        question_concepts.append(q.get("concept_id"))
        if isinstance(qid, str) and not re.fullmatch(r"(?:C\d{2}|S\d{2})-[AB]-\d{2}", qid):
            report.add(path, "questions", "题目编号必须使用 Lxx-A-01 或 Lxx-B-01 格式。")
        elif isinstance(qid, str):
            parts = qid.split("-")
            if parts[0] != lesson_id or q.get("phase") != parts[1] or int(parts[2]) not in numbers:
                report.add(path, "questions", "题目编号必须与课次、阶段和题号一致。")
        options = q.get("options")
        if not isinstance(options, list) or len(options) != 4 or any(not isinstance(x, str) or not x.strip() for x in options):
            report.add(path, "questions", "每题应有四个非空选项。")
        answer = q.get("answer")
        if type(answer) is not int or answer not in range(4):
            report.add(path, "questions", "答案应为 0–3 的选项下标。")
        for key in ("prompt", "explanation"):
            if not isinstance(q.get(key), str) or not q[key].strip():
                report.add(path, "questions", f"缺少 {key}。")
        for word in set(OLD_TERMS):
            prose = " ".join([str(q.get("prompt", "")), *(str(x) for x in options)] if isinstance(options, list) else [str(q.get("prompt", ""))])
            if word in prose:
                report.add(path, "wording", f"学生题干/选项请替换旧说法：{word}")
    if phases.count("A") != 5 or phases.count("B") != 5:
        report.add(path, "questions", "A、B 两阶段各需五题。")
    for concept_id in expected_concept_ids:
        if question_concepts.count(concept_id) != 2:
            report.add(path, "questions", f"知识点 {concept_id} 必须恰好有一道 A 题和一道 B 题。")


def offline_instructor_lessons(root: Path, active: list[str]) -> dict:
    path = root / "active_lessons.json"
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("离线草稿清单须在JSON对象内登记")
    offline = value.get("offline_instructor_lessons", {})
    if not isinstance(offline, dict):
        raise ValueError("offline_instructor_lessons须为明确的课次对象")
    for lesson, entry in offline.items():
        if lesson not in LESSONS or lesson in active or not isinstance(entry, dict):
            raise ValueError("离线草稿课次须合法且不能同时登记为正式活跃课次")
        filename = entry.get("questions")
        if not isinstance(filename, str) or not filename.startswith("questions.draft-") or not filename.endswith(".json"):
            raise ValueError("离线课次须明确登记questions.draft-*.json文件")
        folder = (root / "lessons" / lesson).resolve()
        if not (folder / filename).resolve().is_relative_to(folder):
            raise ValueError("离线草稿题源不能越出本课目录")
        numbers = entry.get("concept_numbers")
        if not isinstance(numbers, list) or len(numbers) != 5 or any(type(n) is not int or not 1 <= n <= 99 for n in numbers) or numbers != sorted(set(numbers)):
            raise ValueError("离线课次须明确登记五个不重复、有序的两位题号")
    return offline


def formal_question_numbers(root: Path, active: list[str]) -> dict:
    """Keep the published S08 revision distinct from historical question IDs."""
    path = root / "active_lessons.json"
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    numbers = value.get("formal_question_numbers", {})
    if not isinstance(numbers, dict):
        raise ValueError("formal_question_numbers须为明确的课次对象")
    # This revision only authorizes S08's new IDs. Other formal lessons retain
    # their original 01–05 constraint; an absent entry also retains that default.
    for lesson, entry in numbers.items():
        if lesson != "S08" or lesson not in active or entry != [11, 12, 13, 14, 15] or any(type(n) is not int for n in entry):
            raise ValueError("仅正式S08新题版本可明确登记11–15题号")
    return numbers


def check_repo(root: Path, profile: str = "auto", expected_count: int | None = None) -> Report:
    root = root.resolve()
    if profile == "auto":
        profile = "planning" if (root / "COURSE_MAP.md").exists() else (
            "student" if (root / "lesson-01/contract.json").exists() or (root / "lessons/C01/contract.json").exists() else "instructor")
    report = Report(root, profile)
    if not root.is_dir():
        report.add(root, "missing", "仓库目录不存在。")
        return report
    required(root / "README.md", report)
    if profile == "planning":
        path = root / "COURSE_MAP.md"
        if required(path, report):
            text = path.read_text()
            ids = re.findall(r"^\|\s*(C\d{2}|S\d{2})\s*\|", text, re.M)
            numbers = None
            if not ids:
                rows = re.findall(r"^###\s+(\d{2})\s*·\s*(C\d{2}|S\d{2})\s*[｜|]", text, re.M)
                numbers = [int(number) for number, _ in rows]
                ids = [lesson for _, lesson in rows]
            if ids != LESSONS or len(ids) != (32 if expected_count is None else expected_count) or (numbers is not None and numbers != list(range(1, 33))):
                report.add(path, "lesson_set", "总表必须按顺序恰好列出 C01、C02 和 S01–S30。")
            report.stats["lessons"] = len(ids)
    else:
        lesson_root = root / "lesson-01" if (root / "lesson-01").is_dir() else root / "lessons"
        folders = sorted(p for p in ((root.glob("lesson-*") if lesson_root == root / "lesson-01" else lesson_root.glob("*"))) if p.is_dir())
        ids = [p.name for p in folders]
        try:
            expected_ids = active_ids(root, "student" if lesson_root.name == "lesson-01" else "instructor")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            report.add(root / "active_lessons.json", "lesson_set", f"活跃课次清单无效：{exc}")
            expected_ids = []
        offline = {}
        formal_numbers = {}
        if profile == "instructor":
            try:
                offline = offline_instructor_lessons(root, expected_ids)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                report.add(root / "active_lessons.json", "offline", f"离线草稿清单无效：{exc}")
            try:
                formal_numbers = formal_question_numbers(root, expected_ids)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                report.add(root / "active_lessons.json", "questions", f"正式题号登记无效：{exc}")
        all_expected = [lesson for lesson in LESSONS if lesson in expected_ids or lesson in offline] if profile == "instructor" else expected_ids
        count = len(all_expected) if expected_count is None else expected_count
        if ids != all_expected or len(ids) != count:
            report.add(lesson_root, "lesson_set", "现行课包目录应与 active_lessons.json 完全一致；完整32课规划单独检查。")
        report.stats["lessons"] = len(folders)
        for folder in folders:
            if profile == "student":
                for name in ["README.md", "LEARN.md", "contract.json", "submission.json"]:
                    required(folder / name, report)
                submission = read_json(folder / "submission.json", report)
                is_template = isinstance(submission, dict) and submission.get("status") == "template"
                if is_template:
                    for name in ["analysis.py", "config.json", "data/base.json", "data/DATA.md"]:
                        required(folder / name, report)
                    if not (folder / "report.md").exists() and not (folder / "update.md").exists():
                        required(folder / "report.md", report)
                path = folder / "README.md"
                if path.exists():
                    headings = re.findall(r"^##\s+(.+)$", path.read_text(), re.M)
                    content_headings = ["作品需要说明的内容" if item == "完成步骤" else item for item in HEADINGS]
                    legacy_layout = headings in [HEADINGS, content_headings, ["90 分钟安排" if item == "课堂任务" else item for item in HEADINGS]]
                    # Reviewed numeric lessons use task-specific headings and linked support.
                    text = path.read_text()
                    flexible_layout = (folder.name.startswith("lesson-") and len(headings) >= 3
                                       and len(headings) == len(set(headings))
                                       and "LEARN.md" in text and "SUPPORT.md" in text
                                       and any(word in text for word in ("标准任务", "本课必做", "标准项目", "课堂任务")))
                    if not (legacy_layout or flexible_layout):
                        report.add(path, "headings", "课次 README 需有清楚的任务分节，并链接学习与操作支持；旧模板仍可用原七节结构。")
                check_submission(folder, report)
                for name in ["config.json", "data/base.json"]:
                    if (folder / name).exists():
                        read_json(folder / name, report)
            else:
                entry = offline.get(folder.name)
                question_file = entry["questions"] if entry else "questions.json"
                for name in ["RUNBOOK.md", "REFERENCE.md", question_file]:
                    required(folder / name, report)
                path = folder / question_file
                check_question_set(read_json(path, report), path, report, folder.name, concept_numbers=entry["concept_numbers"] if entry else formal_numbers.get(folder.name))
    for path in root.rglob("*"):
        if any(part in (".git", ".venv", "__pycache__", ".pytest_cache", "artifacts", "archives") for part in path.relative_to(root).parts):
            continue
        if not path.is_file():
            continue
        if not path.resolve().is_relative_to(root):
            report.add(path, "path", "课程材料不应通过符号链接读取仓库外文件。")
            continue
        if path.suffix == ".md":
            check_prose(path, report, student=profile in ("student", "planning"))
        elif path.suffix == ".py":
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (SyntaxError, UnicodeError) as exc:
                report.add(path, "python", f"Python 语法错误：{exc}")
    return report


def run_cli(argv=None) -> int:
    parser = argparse.ArgumentParser(description="检查课程材料的结构；不执行学生代码，不选择模型或判断结论。")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--profile", choices=("auto", "student", "instructor", "planning"), default="auto")
    parser.add_argument("--expected-count", type=int, default=None, help="可选覆盖；默认规划32课，课包按活跃清单")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = check_repo(args.repo, args.profile, args.expected_count)
    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"{report.profile}: {report.stats.get('lessons', 0)} 课；{len(report.issues)} 项需处理。")
        for issue in report.issues:
            print(f"{issue['severity']} {issue['path']} [{issue['code']}]: {issue['message']}")
        print("这是结构检查；项目判断与结论依据由人阅读，未执行提交命令。")
    return 1 if report.failed(args.strict) else 0
