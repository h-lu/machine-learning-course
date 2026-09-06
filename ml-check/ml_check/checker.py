"""Check material structure without running submitted commands or judging choices."""
from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

LESSONS = ["C01", "C02"] + [f"S{i:02d}" for i in range(1, 31)]
HEADINGS = ["本课要解决什么问题", "本课要学会什么", "90 分钟安排", "完成步骤",
            "必须提交什么", "不同起点怎么做", "运行限制"]
TASK_FIELDS = ["question", "user", "data_source", "metric", "split_plan", "initial_expectation"]
# Scan current student prose, not archives, field names or historical explanations.
OLD_TERMS = ["问题契约", "知识自查", "使用决定", "输入契约", "指标契约", "MDP 契约",
             "知识自查", "门禁", "签收", "消费测试集", "运行前预测", "样本单位", "预测时点",
             "适用边界", "委托", "红组", "蓝组", "负责决定", "适用范围", "结果记录",
             "锁定", "行动规则", "错误代价", "回退/撤回"]


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
        for word in set(OLD_TERMS):
            if word in text:
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
    for obj, path in [(task, task_path), (sub, sub_path)]:
        if obj.get("lesson_id") != folder.name:
            report.add(path, "lesson_id", "课次编号应与目录相同。")
    for key in TASK_FIELDS:
        if not isinstance(task.get(key), str):
            report.add(task_path, "task", f"任务说明需要文字字段 {key}。")
    status = sub.get("status")
    if status not in ("template", "in_progress", "complete"):
        report.add(sub_path, "status", "状态应为 template、in_progress 或 complete。")
    if not isinstance(sub.get("run"), str) or not sub["run"].strip():
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


def check_question_set(value, path: Path, report: Report, lesson_id: str) -> None:
    if not isinstance(value, dict) or value.get("lesson_id") != lesson_id:
        report.add(path, "questions", "题目课次与目录不一致。")
        return
    questions = value.get("questions")
    if not isinstance(questions, list) or len(questions) != 4:
        report.add(path, "questions", "每课需要 A、B 各两道概念题。")
        return
    seen, phases = set(), []
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
    if phases.count("A") != 2 or phases.count("B") != 2:
        report.add(path, "questions", "A、B 两阶段各需两题。")


def check_repo(root: Path, profile: str = "auto", expected_count: int = 32) -> Report:
    root = root.resolve()
    if profile == "auto":
        profile = "planning" if (root / "COURSE_MAP.md").exists() else (
            "student" if (root / "lessons/C01/contract.json").exists() else "instructor")
    report = Report(root, profile)
    if not root.is_dir():
        report.add(root, "missing", "仓库目录不存在。")
        return report
    required(root / "README.md", report)
    if profile == "planning":
        path = root / "COURSE_MAP.md"
        if required(path, report):
            ids = re.findall(r"^\|\s*(C\d{2}|S\d{2})\s*\|", path.read_text(), re.M)
            if ids != LESSONS or len(ids) != expected_count:
                report.add(path, "lesson_set", "总表必须按顺序恰好列出 C01、C02 和 S01–S30。")
            report.stats["lessons"] = len(ids)
    else:
        folders = sorted(p for p in (root / "lessons").glob("*") if p.is_dir())
        ids = [p.name for p in folders]
        if ids != LESSONS or len(ids) != expected_count:
            report.add(root / "lessons", "lesson_set", "目录应恰好包含 C01、C02 和 S01–S30，共 32 课。")
        report.stats["lessons"] = len(folders)
        for folder in folders:
            if profile == "student":
                for name in ["README.md", "LEARN.md", "contract.json", "submission.json"]:
                    required(folder / name, report)
                submission = read_json(folder / "submission.json", report)
                is_template = isinstance(submission, dict) and submission.get("status") == "template"
                if is_template:
                    for name in ["analysis.py", "config.json", "data/base.json", "data/DATA.md", "update.md"]:
                        required(folder / name, report)
                path = folder / "README.md"
                if path.exists():
                    headings = re.findall(r"^##\s+(.+)$", path.read_text(), re.M)
                    if headings != HEADINGS:
                        report.add(path, "headings", "课次 README 应依次使用课程规范中的七个二级标题。")
                check_submission(folder, report)
                for name in ["config.json", "data/base.json"]:
                    if (folder / name).exists():
                        read_json(folder / name, report)
            else:
                for name in ["RUNBOOK.md", "REFERENCE.md", "questions.json"]:
                    required(folder / name, report)
                path = folder / "questions.json"
                check_question_set(read_json(path, report), path, report, folder.name)
    for path in root.rglob("*"):
        if any(part in (".git", ".venv", "__pycache__", ".pytest_cache", "artifacts") for part in path.relative_to(root).parts):
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
    parser.add_argument("--expected-count", type=int, default=32)
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
