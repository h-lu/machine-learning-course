import json
import tempfile
import unittest
from pathlib import Path

from ml_check.checker import HEADINGS, LESSONS, Report, check_repo, check_submission, read_json


class SubmissionChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / "lessons/C01"
        self.folder.mkdir(parents=True)
        self.task = {key: "自选问题的解释" for key in ("question", "user", "data_source", "metric", "split_plan", "initial_expectation")}
        self.task["lesson_id"] = "C01"
        self.sub = dict(lesson_id="C01", status="complete", run="python3 my_experiment.py", report="my_report.md", artifacts=["numbers.csv"])
        (self.root / "my_report.md").write_text("比较两个方案后，我建议暂时不使用模型。依据在生成的表中。")
        (self.root / "numbers.csv").write_text("method,error\nrule,2\nmodel,4\n")

    def check(self):
        (self.folder / "contract.json").write_text(json.dumps(self.task))
        (self.folder / "submission.json").write_text(json.dumps(self.sub))
        report = Report(self.root, "student")
        check_submission(self.folder, report)
        return report

    def test_independent_run_report_and_csv_are_accepted(self):
        self.assertFalse(self.check().failed(True))

    def test_opposite_decisions_and_arbitrary_metrics_are_accepted(self):
        for metric in ["每周漏掉的事件数", "响应超过两秒的比例", "未找到证据时的拒答率"]:
            for conclusion in ["采用规则", "采用神经网络", "暂时停止使用"]:
                self.task["metric"] = metric
                (self.root / "my_report.md").write_text(conclusion)
                self.assertFalse(self.check().failed(True))

    def test_does_not_execute_submitted_commands(self):
        sentinel = self.root / "should-not-exist"
        self.sub["run"] = f"touch {sentinel}"
        self.check()
        self.assertFalse(sentinel.exists())

    def test_template_does_not_claim_completion(self):
        self.sub["status"] = "template"
        for key in self.task:
            if key != "lesson_id":
                self.task[key] = ""
        (self.root / "numbers.csv").unlink()
        report = self.check()
        self.assertFalse(report.failed(True))
        self.assertEqual(report.stats["template"], 1)

    def test_completed_submission_requires_task_and_artifact(self):
        self.task["metric"] = ""
        (self.root / "numbers.csv").unlink()
        codes = {x["code"] for x in self.check().issues}
        self.assertIn("incomplete", codes)
        self.assertIn("missing", codes)

    def test_report_cannot_escape_repo(self):
        self.sub["report"] = "../outside.md"
        self.assertTrue(any(x["code"] == "path" for x in self.check().issues))

    def test_symlink_cannot_escape_repo(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "report.md"
            target.write_text("outside")
            (self.root / "link.md").symlink_to(target)
            self.sub["report"] = "link.md"
            self.assertTrue(any(x["code"] == "path" for x in self.check().issues))

    def test_wrong_field_types_report_errors(self):
        self.sub["artifacts"] = "numbers.csv"
        self.task["metric"] = ["not a string"]
        self.assertTrue(self.check().failed())

    def test_full_repo_accepts_replacement_of_default_entry_and_data_layout(self):
        (self.root / "README.md").write_text("# 学生项目")
        self.check()
        for lesson in LESSONS:
            p = self.root / "lessons" / lesson
            p.mkdir(exist_ok=True)
            (p / "README.md").write_text("\n\n".join("## " + title + "\n\n具体解释。" for title in HEADINGS))
            (p / "LEARN.md").write_text("# 学习材料\n\n这里解释本课的例子。")
            (p / "contract.json").write_text(json.dumps({**self.task, "lesson_id": lesson}))
            (p / "submission.json").write_text(json.dumps({**self.sub, "lesson_id": lesson}))
        report = check_repo(self.root, "student")
        self.assertFalse(report.failed(True), report.issues)

    def test_nonfinite_json_is_rejected(self):
        path = self.root / "bad.json"
        path.write_text('{"score":NaN}')
        report = Report(self.root, "student")
        self.assertIsNone(read_json(path, report))
        self.assertTrue(report.failed())


class PlanningChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "README.md").write_text("# 课程")
        self.write_map(LESSONS)

    def write_map(self, ids):
        (self.root / "COURSE_MAP.md").write_text("\n".join(f"| {id} | 内容 |" for id in ids))

    def test_exact_32_lessons(self):
        self.assertFalse(check_repo(self.root, "planning").failed(True))

    def test_duplicate_or_missing_lesson_fails(self):
        self.write_map(LESSONS[:-1] + ["S29"])
        self.assertTrue(check_repo(self.root, "planning").failed(True))

    def test_broken_link_fails(self):
        (self.root / "README.md").write_text("[打开不存在文件](missing.md)")
        self.assertIn("link", {x["code"] for x in check_repo(self.root, "planning").issues})

    def test_old_student_wording_fails(self):
        (self.root / "README.md").write_text("请填写问题契约。")
        self.assertIn("wording", {x["code"] for x in check_repo(self.root, "planning").issues})

    def test_syntax_error_fails_without_importing_script(self):
        (self.root / "broken.py").write_text("def f(:\n")
        self.assertIn("python", {x["code"] for x in check_repo(self.root, "planning").issues})


if __name__ == "__main__":
    unittest.main()
