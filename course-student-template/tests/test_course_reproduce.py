"""Exercise completed student projects through the real reproduction CLI."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = "lesson-01/artifacts/comparison/chosen"


class CourseReproductionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="student-reproduction-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        (self.root / "scripts").mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/course.py", self.root / "scripts/course.py")
        (self.root / "mlcourse").mkdir()
        shutil.copy2(ROOT / "mlcourse/bike_starter.py", self.root / "mlcourse/bike_starter.py")
        (self.root / "lesson-01").mkdir()
        self.write_json("active_lessons.json", {"active_student_lessons": ["lesson-01"]})
        self.write_json("lesson-01/inputs.json", {
            "train_x": [0, 1, 2], "train_y": [4, 7, 10],
            "validation_x": [3, 4], "validation_y": [13, 15],
        })
        (self.root / "lesson-01/report.md").write_text(
            "自选线性规则在另外两条样本上的 MAE 为 0.5。\n", encoding="utf-8")
        self.artifacts = [f"{OUTPUT}/records.csv", f"{OUTPUT}/summary.json"]
        self.submission = {
            "lesson": "lesson-01", "status": "complete", "report": "lesson-01/report.md",
            "artifacts": self.artifacts, "run": ["python", "lesson-01/project.py"],
        }
        self.write_json("lesson-01/submission.json", self.submission)
        self.write_program()
        result = self.invoke("lesson-01/project.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def write_json(self, relative, value):
        (self.root / relative).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def write_program(self, checks=""):
        code = textwrap.dedent('''\
            from pathlib import Path
            import json
            import sys
            root = Path(__file__).resolve().parents[1]
            sys.path.insert(0, str(root))
            from mlcourse.bike_starter import fit_simple_line, mae, save_results
            inputs = json.loads((root / "lesson-01/inputs.json").read_text(encoding="utf-8"))
            intercept, slope = fit_simple_line(inputs["train_x"], inputs["train_y"])
            predicted = [intercept + slope * x for x in inputs["validation_x"]]
            records = [{"x": x, "actual": y, "prediction": p}
                       for x, y, p in zip(inputs["validation_x"], inputs["validation_y"], predicted)]
            summary = {"intercept": intercept, "slope": slope,
                       "mae": mae(inputs["validation_y"], predicted)}
            ''')
        code += checks + f'\nsave_results(root / "{OUTPUT}", records, summary)\n'
        (self.root / "lesson-01/project.py").write_text(code, encoding="utf-8")

    def invoke(self, *args):
        return subprocess.run([sys.executable, *args], cwd=self.root, capture_output=True, text=True)

    def snapshot(self):
        return {path.relative_to(self.root).as_posix(): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()}

    def test_nested_save_results_reproduces_identical_bytes(self):
        summary = json.loads((self.root / self.artifacts[1]).read_text(encoding="utf-8"))
        self.assertEqual(summary, {"intercept": 4.0, "slope": 3.0, "mae": 0.5})
        # All artifact ancestors are empty after deleting the listed outputs.
        self.write_program('assert not (root / "lesson-01/artifacts").exists()\n')
        before = self.snapshot()
        result = self.invoke("scripts/course.py", "ci")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_no_op_cannot_pass_by_reusing_submitted_outputs(self):
        self.submission["run"] = ["python", "-c", "pass"]
        self.write_json("lesson-01/submission.json", self.submission)
        before = self.snapshot()
        result = self.invoke("scripts/course.py", "ci")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("结果文件不存在或为空", result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_unlisted_evidence_source_and_empty_child_survive_in_scratch(self):
        parent = self.root / "lesson-01/artifacts/comparison"
        (parent / "notes.md").write_bytes(b"keep this unlisted evidence\n")
        (parent / "helper.py").write_bytes(b"def student_choice(): return 17\n")
        (parent / "unlisted-empty").mkdir()
        self.write_program(textwrap.dedent('''\
            parent = root / "lesson-01/artifacts/comparison"
            assert (parent / "notes.md").read_bytes() == b"keep this unlisted evidence\\n"
            assert (parent / "helper.py").read_bytes() == b"def student_choice(): return 17\\n"
            assert (parent / "unlisted-empty").is_dir()
            assert not (parent / "chosen").exists()
            '''))
        before = self.snapshot()
        result = self.invoke("scripts/course.py", "ci")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertTrue((parent / "unlisted-empty").is_dir())

    def test_unlisted_file_in_output_prevents_pruning_and_failed_run_preserves_original(self):
        (self.root / OUTPUT / "keep.bin").write_bytes(b"\x00unlisted evidence\xff")
        self.write_program(textwrap.dedent(f'''\
            output = root / "{OUTPUT}"
            assert (output / "keep.bin").read_bytes() == b"\\x00unlisted evidence\\xff"
            assert not (output / "records.csv").exists()
            assert not (output / "summary.json").exists()
            '''))
        before = self.snapshot()
        result = self.invoke("scripts/course.py", "ci")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("结果目录已存在", result.stderr)
        self.assertNotIn("AssertionError", result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_changed_result_fails_digest_check_and_preserves_original(self):
        self.write_json("lesson-01/inputs.json", {
            "train_x": [0, 1, 2], "train_y": [4, 7, 10],
            "validation_x": [3, 4], "validation_y": [13, 16],
        })
        before = self.snapshot()
        result = self.invoke("scripts/course.py", "ci")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("重新运行得到的结果与已提交文件不同", result.stderr)
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
