"""回归检查学生文档中的操作路径；不是对真人可读性的自动评分。"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.intro import example_config, example_data
from mlcourse.runtime import intro_console_summary, run_experiment


def command(args, cwd, *, check=True):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    return subprocess.run(args, cwd=cwd, text=True, encoding="utf-8", capture_output=True,
                          check=check, timeout=60, env=env)


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class ColdReadOutput(unittest.TestCase):
    def test_c01_starts_with_one_prediction_not_an_unexplained_mae(self):
        result = run_experiment("C01", example_data("C01"), example_config("C01"))
        text = intro_console_summary(result)
        self.assertIn("train-03", text)
        self.assertIn("预测 = 5 分钟；绝对误差 = 1 分钟", text)
        self.assertIn("不训练", text)
        self.assertNotIn("MAE =", text)
        self.assertIn("null 表示没有值，不是误差为 0", text)

    def test_c02_names_all_models_and_group_denominators(self):
        result = run_experiment("C02", example_data("C02"), example_config("C02"))
        text = intro_console_summary(result)
        for label, value in [("均值基线", "1.25"), ("人工规则", "0.75"), ("一元线性回归", "0.75")]:
            self.assertIn(f"{label}：MAE = {value} 分钟", text)
        self.assertIn("午间，3 条", text)
        self.assertIn("晚间，1 条", text)
        self.assertIn("不是自动推荐", text)
        self.assertIn("validation-03", text)

    def test_changed_rule_can_keep_same_mae_but_changes_sample_predictions(self):
        config = example_config("C02")
        before = run_experiment("C02", example_data("C02"), config)
        config["rule_slope"] = 1.5
        after = run_experiment("C02", example_data("C02"), config)
        self.assertEqual(before["comparison"]["rule"]["mae"], after["comparison"]["rule"]["mae"])
        self.assertNotEqual(before["details"]["predictions"], after["details"]["predictions"])
        self.assertIn("人工规则预测 = 4 分钟", intro_console_summary(after))
        self.assertEqual(before["metrics"], after["metrics"])


class ColdReadWalkthrough(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "student"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", ".venv", "artifacts", "__pycache__", ".pytest_cache"))

    def py(self, *args, check=True):
        return command([sys.executable, *args], self.root, check=check)

    def payload(self, relative):
        return json.loads((self.root / relative / "summary.json").read_text(encoding="utf-8"))

    def prepare_completed_lessons(self):
        for n in (1, 2):
            lesson = f"lesson-{n:02d}"
            folder = self.root / lesson
            self.py("scripts/course.py", "start", str(n))
            if n == 2:
                config = example_config("C02")
                write_json(folder / "config-validation.json", config)
                self.py(f"{lesson}/analysis.py", "--config", f"{lesson}/config-validation.json",
                        "--split", "validation", "--output", f"{lesson}/artifacts/validation")
                config["evaluation_split"] = "test"
                write_json(folder / "config.json", config)
            self.py("scripts/course.py", "run", str(n))
            task = json.loads((folder / "contract.json").read_text(encoding="utf-8"))
            task.update(question="用人数预测等候分钟数", user="练习中的取餐同学", data_source="人工教学样本",
                        metric="逐条绝对误差；第二课再比较 MAE，单位分钟", split_plan="按课内安排核对样本或划分数据",
                        initial_expectation="测试文件操作的示例说明，不是学生真实作业")
            write_json(folder / "contract.json", task)
            (folder / "report.md").write_text("# 流程测试用报告\n本文件只用于检查提交与重跑，不能作为学生成果。\n", encoding="utf-8")
            sub = json.loads((folder / "submission.json").read_text(encoding="utf-8"))
            sub["status"] = "complete"
            write_json(folder / "submission.json", sub)
            self.py("scripts/course.py", "check", str(n))

    def test_c01_readme_configuration_and_commands_run_in_order(self):
        text = (self.root / "lesson-01/README.md").read_text(encoding="utf-8")
        example = json.loads(re.search(r"```json\n(.*?)\n```", text, re.S).group(1))
        for args in [("scripts/course.py", "start", "01"), ("scripts/course.py", "run", "01")]:
            self.assertIn("python " + " ".join(args), text)
            self.py(*args)
        old = (self.root / "lesson-01/artifacts/predictions.csv").read_bytes()
        write_json(self.root / "lesson-01/config-trial.json", example)
        args = ["lesson-01/analysis.py", "--config", "lesson-01/config-trial.json", "--output", "lesson-01/artifacts/trial"]
        self.assertIn("python " + " ".join(args), text)
        self.py(*args)
        row = self.payload("lesson-01/artifacts/trial")["details"]["predictions"][2]
        self.assertEqual(row["prediction_rule"], 4)
        self.assertEqual(row["absolute_error_rule"], 0)
        self.assertEqual(old, (self.root / "lesson-01/artifacts/predictions.csv").read_bytes())
        example["stress_queue"] = 6
        write_json(self.root / "lesson-01/config-trial.json", example)
        result = self.py(*args)
        self.assertIn("新输入检查：6 人", result.stdout)
        self.assertIsNone(self.payload("lesson-01/artifacts/trial")["stress_test"]["metrics"]["mae"])

    def test_invalid_input_names_config_field_and_does_not_refresh_old_results(self):
        self.py("scripts/course.py", "run", "01")
        output = self.root / "lesson-01/artifacts/summary.json"
        before = output.read_bytes()
        config = example_config("C01"); config["stress_queue"] = -1
        write_json(self.root / "lesson-01/config-invalid.json", config)
        failed = self.py("lesson-01/analysis.py", "--config", "lesson-01/config-invalid.json", check=False)
        self.assertEqual(failed.returncode, 2)
        self.assertIn("stress_queue", failed.stderr)
        self.assertIn("以前的运行", failed.stderr)
        self.assertNotIn("示例实验已运行", failed.stdout)
        self.assertEqual(before, output.read_bytes())

    def test_json_error_names_file_and_line(self):
        (self.root / "lesson-01/config-invalid.json").write_text('{\n"rule_slope":1.5,\n}', encoding="utf-8")
        result = self.py("lesson-01/analysis.py", "--config", "lesson-01/config-invalid.json", check=False)
        self.assertEqual(result.returncode, 2)
        invalid = (self.root / "lesson-01/config-invalid.json").read_text(encoding="utf-8")
        try:
            json.loads(invalid)
        except json.JSONDecodeError as error:
            self.assertIn(f"config-invalid.json 第 {error.lineno} 行第 {error.colno} 列", result.stderr)
        else:
            self.fail("The test input must be invalid JSON")
        self.assertIn("英文双引号", result.stderr)
        self.assertFalse((self.root / "lesson-01/artifacts").exists())

    def test_c02_validation_survives_test_and_rechecks_from_saved_config(self):
        text = (self.root / "lesson-02/README.md").read_text(encoding="utf-8")
        self.py("scripts/course.py", "start", "02")
        runs = re.findall(r"^python (lesson-02/analysis.py .+)$", text, re.M)
        self.py(*shlex.split(runs[0]))
        config = example_config("C02"); config["rule_slope"] = 1.5; config["stress_queue"] = 6
        write_json(self.root / "lesson-02/config-trial.json", config)
        self.py(*shlex.split(runs[1]))
        original = (self.root / "lesson-02/artifacts/validation-original/predictions.csv").read_bytes()
        write_json(self.root / "lesson-02/config-validation.json", config)
        self.py(*shlex.split(runs[2]))
        before = {p.name: p.read_bytes() for p in (self.root / "lesson-02/artifacts/validation").iterdir()}
        config["evaluation_split"] = "test"
        write_json(self.root / "lesson-02/config.json", config)
        self.py("scripts/course.py", "run", "02")
        self.assertEqual(self.payload("lesson-02/artifacts")["metrics"]["n"], 6)
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.root / "lesson-02/artifacts/validation").iterdir()})
        self.assertEqual(original, (self.root / "lesson-02/artifacts/validation-original/predictions.csv").read_bytes())
        self.py(*shlex.split(runs[3]))
        after = {p.name: p.read_bytes() for p in (self.root / "lesson-02/artifacts/recheck-validation").iterdir()}
        self.assertEqual(before, after)
        sub = json.loads((self.root / "lesson-02/submission.json").read_text(encoding="utf-8"))
        self.assertEqual(sub["status"], "in_progress")

    @unittest.skipUnless(shutil.which("git"), "Git is needed to verify submission tracking")
    def test_documented_git_add_includes_results_and_clean_clone_reproduces(self):
        command(["git", "init", "-q"], self.root)
        command(["git", "config", "user.name", "Course test"], self.root)
        command(["git", "config", "user.email", "course-test@example.invalid"], self.root)
        command(["git", "add", "."], self.root)
        command(["git", "commit", "-qm", "Template for local submission test"], self.root)
        self.prepare_completed_lessons()
        for n in (1, 2):
            relative = f"lesson-{n:02d}/artifacts/summary.json"
            self.assertEqual(command(["git", "check-ignore", relative], self.root).stdout.strip(), relative)
        guide = (self.root / "docs/FIRST_RUN.md").read_text(encoding="utf-8")
        # Execute only staging commands: never push to a remote or create classroom tags in tests.
        for args in re.findall(r"^git add (.+)$", guide, re.M):
            command(["git", "add", *shlex.split(args)], self.root)
        staged = set(command(["git", "diff", "--cached", "--name-only"], self.root).stdout.splitlines())
        required = {f"lesson-{n:02d}/artifacts/{file}" for n in (1, 2) for file in ("summary.json", "predictions.csv")}
        required |= {f"lesson-02/artifacts/validation/{file}" for file in ("summary.json", "predictions.csv")}
        self.assertTrue(required <= staged)
        command(["git", "commit", "-qm", "Completed local workflow fixture"], self.root)
        clone = Path(self.temp.name) / "fresh-clone"
        command(["git", "clone", "-q", "--local", str(self.root), str(clone)], self.root)
        for file in required:
            self.assertTrue((clone / file).is_file(), file)
        command([sys.executable, "scripts/course.py", "ci"], clone)
        self.assertEqual(command(["git", "status", "--porcelain"], clone).stdout, "")


if __name__ == "__main__":
    unittest.main()
