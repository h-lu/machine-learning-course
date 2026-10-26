"""Exercise the documented temporary updater against disposable local Git releases."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "docs/LESSONS13_14_FILES.json"
UPDATER = "scripts/course_l1314.py"
MODEL = "data/sms/encoder/onnx/model_quint8_avx2.onnx"
OLD_COURSE_SHA = "8e9e9c412ad866ebe9cc431ef19f8362186c837efe459ac1e5fa849e95014118"
NEW_COURSE_SHA = "bcdc83ee2be99e018d8511ca704316c9d0083d1ecb310f06f82a42b63061b7c2"
OLD_UPDATER_SHA = "0b153d841b2c80b47eddc87d2492a151591cfc55cc303cef9a7d8ccc3425c876"
MODEL_SHA = "7b411e18f5974428b388be5667cf76d57c2a52968e1d6b0153a30a8ccfb34204"
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", GIT_CONFIG_NOSYSTEM="1",
           GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(
        ["git", "-c", "user.name=Sync test", "-c", "user.email=sync@example.invalid",
         "-c", "commit.gpgsign=false", "-C", str(root), *args],
        env=ENV, stderr=subprocess.DEVNULL,
    )


def snapshot(root):
    """Include contents, directories, symlinks and mtimes, including .git files."""
    result = {}
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root).as_posix()
        stat = path.lstat()
        if path.is_symlink():
            result[name] = ("symlink", os.readlink(path), stat.st_mtime_ns)
        elif path.is_file():
            result[name] = ("file", digest(path.read_bytes()), stat.st_mtime_ns)
        else:
            result[name] = ("directory", stat.st_mtime_ns)
    return result


class Lesson1314SyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release_temp = tempfile.TemporaryDirectory(prefix="ml1314-release-")
        cls.addClassCleanup(cls.release_temp.cleanup)
        cls.release = Path(cls.release_temp.name) / "release"
        cls.release.mkdir()
        cls.info = json.loads((ROOT / MANIFEST).read_text())
        cls.old_course = (ROOT / "tests/fixtures/course_pre_sync.py").read_bytes()
        cls.new_course = (ROOT / "tests/fixtures/course_6f97c4ff.py.fixture").read_bytes()
        cls.old_updater = (ROOT / "tests/fixtures/course_l1314_before_compat.py.fixture").read_bytes()
        assert digest(cls.old_course) == OLD_COURSE_SHA
        assert digest(cls.new_course) == NEW_COURSE_SHA
        assert digest(cls.old_updater) == OLD_UPDATER_SHA
        paths = set(cls.info["files"]) | set(cls.info["required_existing"]) | {MANIFEST}
        for name in paths:
            target = cls.release / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        git(cls.release, "init", "-b", "main")
        git(cls.release, "add", ".")
        git(cls.release, "commit", "-m", "Exact local release fixture")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ml1314-student-")
        self.addCleanup(self.temp.cleanup)
        self.temp_root = Path(self.temp.name)
        self.student_number = 0

    def student(self, course="old", updater="missing"):
        self.student_number += 1
        root = self.temp_root / f"student-{self.student_number}"
        # Local shared objects avoid repeatedly copying the real 17 MB model.
        git(self.temp_root, "clone", "--shared", "--no-checkout", "-o", "course-release",
            str(self.release), str(root))
        for name in self.info["required_existing"]:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())
        (root / "scripts/course.py").write_bytes(
            self.old_course if course == "old" else self.new_course)
        if updater != "missing":
            (root / UPDATER).write_bytes(
                self.old_updater if updater == "old" else (ROOT / UPDATER).read_bytes())
        activation = {
            "active_student_lessons": [f"lesson-{n:02d}" for n in range(1, 13)],
            "active_instructor_lessons": ["S05"],
            "custom": {"keep": [3, 2, 1]},
        }
        (root / "active_lessons.json").write_text(json.dumps(activation, indent=4) + "\n")
        (root / "lesson-12").mkdir()
        (root / "lesson-12/report.md").write_text("Uncommitted student report\n")
        return root

    def run_updater(self, root):
        # This is the documented bootstrap: read the new release entry into a
        # temporary file, without replacing either installed student script.
        helper = self.temp_root / "temporary-course_l1314.py"
        helper.write_bytes(git(root, "show", "course-release/main:" + UPDATER))
        return subprocess.run(
            [sys.executable, str(helper), "sync", "--destination", str(root)],
            cwd=root, env=ENV, text=True, capture_output=True, timeout=30,
        )

    def assert_success(self, root):
        result = self.run_updater(root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_rejected_without_writes(self, root, message):
        before = snapshot(root)
        result = self.run_updater(root)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(message, result.stdout + result.stderr)
        self.assertEqual(snapshot(root), before)

    def change_remote(self, root, name, data):
        changed = self.temp_root / "changed-release"
        git(self.temp_root, "clone", "--shared", str(self.release), str(changed))
        (changed / name).write_bytes(data)
        git(changed, "add", "--", name)
        git(changed, "commit", "-m", "Intentionally inconsistent test release")
        git(root, "remote", "set-url", "course-release", str(changed))
        git(root, "fetch", "course-release", "main")

    def test_manifest_keeps_all_release_hashes_and_only_two_course_versions(self):
        self.assertEqual(len(self.info["files"]), 51)
        self.assertEqual(len(self.info["required_existing"]), 7)
        self.assertEqual(set(self.info["required_existing"]["scripts/course.py"]),
                         {OLD_COURSE_SHA, NEW_COURSE_SHA})
        self.assertIn(digest((ROOT / "scripts/course.py").read_bytes()),
                      self.info["required_existing"]["scripts/course.py"])
        self.assertEqual(self.info["compatible_existing_updater_sha256"], [OLD_UPDATER_SHA])
        for name, expected in self.info["files"].items():
            self.assertEqual(digest((ROOT / name).read_bytes()), expected, name)
        for name, expected in self.info["required_existing"].items():
            if name != "scripts/course.py":
                self.assertIsInstance(expected, str)
                self.assertEqual(digest((ROOT / name).read_bytes()), expected, name)
        self.assertEqual(digest((ROOT / UPDATER).read_bytes()), self.info["files"][UPDATER])
        model = (ROOT / MODEL).read_bytes()
        self.assertEqual(len(model), 17490869)
        self.assertEqual(digest(model), MODEL_SHA)
        self.assertFalse(model.startswith(b"version https://git-lfs.github.com/spec/v1"))
        self.assertFalse(model.lstrip().lower().startswith((b"<!doctype html", b"<html")))

    def test_both_course_versions_and_all_installed_updater_states_sync_twice(self):
        for course in ("old", "new"):
            for updater in ("missing", "old", "new"):
                with self.subTest(course=course, updater=updater):
                    root = self.student(course, updater)
                    before = snapshot(root)
                    old_activation = json.loads((root / "active_lessons.json").read_text())
                    self.assert_success(root)
                    after = snapshot(root)
                    for name, state in before.items():
                        if state[0] == "file" and name != "active_lessons.json":
                            self.assertEqual(after[name], state, name)
                    for name, expected in self.info["files"].items():
                        actual = digest((root / name).read_bytes())
                        if name == UPDATER and updater == "old":
                            self.assertEqual(actual, OLD_UPDATER_SHA)
                        else:
                            self.assertEqual(actual, expected, name)
                    activation = json.loads((root / "active_lessons.json").read_text())
                    self.assertEqual(activation, dict(
                        old_activation,
                        active_student_lessons=old_activation["active_student_lessons"]
                        + ["lesson-13", "lesson-14"]))
                    first = snapshot(root)
                    self.assert_success(root)
                    self.assertEqual(snapshot(root), first)

    def test_existing_student_lesson_directories_are_preserved_as_a_whole(self):
        root = self.student(updater="old")
        personal = {}
        for number in (13, 14):
            for name in ("README.md", "report.md", "submission.json", "artifacts/my-result.csv"):
                path = root / f"lesson-{number}" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"personal unfinished lesson {number}: {name}\n")
                personal[path.relative_to(root).as_posix()] = path.read_bytes()
        self.assert_success(root)
        for name, data in personal.items():
            self.assertEqual((root / name).read_bytes(), data)
        for number in (13, 14):
            self.assertFalse((root / f"lesson-{number}/analysis.py").exists())
        first = snapshot(root)
        self.assert_success(root)
        self.assertEqual(snapshot(root), first)

    def test_unknown_course_script_is_rejected_without_writes(self):
        root = self.student()
        (root / "scripts/course.py").write_bytes(self.old_course + b"\n# Personal changes\n")
        self.assert_rejected_without_writes(root, "Prerequisite differs or missing: scripts/course.py")

    def test_unknown_installed_updater_is_rejected_without_writes(self):
        root = self.student(updater="old")
        (root / UPDATER).write_bytes(self.old_updater + b"\n# Personal changes\n")
        self.assert_rejected_without_writes(root, "Existing shared file differs")

    def test_changed_shared_file_is_rejected_without_writes(self):
        root = self.student()
        (root / "mlcourse/transfer13.py").write_text("personal shared module\n")
        self.assert_rejected_without_writes(root, "Existing shared file differs")

    def test_changed_local_model_is_rejected_without_writes(self):
        root = self.student(updater="old")
        model = root / MODEL
        model.parent.mkdir(parents=True)
        model.write_bytes(b"not the approved model")
        self.assert_rejected_without_writes(root, "Existing shared file differs")

    def test_bad_remote_model_is_rejected_without_writes(self):
        root = self.student(updater="old")
        self.change_remote(root, MODEL, b"not the approved model")
        self.assert_rejected_without_writes(root, "Release identity mismatch: " + MODEL)

    def test_legacy_updater_exception_never_skips_remote_self_hash(self):
        root = self.student(updater="old")
        self.change_remote(root, UPDATER, (ROOT / UPDATER).read_bytes() + b"\n# Release tamper\n")
        self.assert_rejected_without_writes(root, "Release identity mismatch: " + UPDATER)

    def test_invalid_active_metadata_is_rejected_before_any_writes(self):
        invalid = [
            "{", "[]", "{}", '{"active_student_lessons": null}',
            '{"active_student_lessons": "lesson-01"}',
            '{"active_student_lessons": [1]}',
            '{"active_student_lessons": ["lesson-01", "lesson-01"]}',
            '{"active_student_lessons": ["lesson-1"]}',
        ]
        for text in invalid:
            with self.subTest(text=text):
                root = self.student(updater="old")
                (root / "active_lessons.json").write_text(text)
                self.assert_rejected_without_writes(root, "")

    def test_active_symlink_is_rejected_without_touching_its_target(self):
        root = self.student()
        active = root / "active_lessons.json"
        outside = self.temp_root / "personal-active.json"
        outside.write_bytes(active.read_bytes())
        active.unlink()
        active.symlink_to(outside)
        before = outside.read_bytes(), outside.stat().st_mtime_ns
        self.assert_rejected_without_writes(root, "active_lessons.json")
        self.assertEqual((outside.read_bytes(), outside.stat().st_mtime_ns), before)

    def test_parent_file_is_rejected_before_any_writes(self):
        root = self.student()
        # Keep every prerequisite valid: without parent preflight, earlier
        # pending model/cache files would be written before docs.mkdir fails.
        (root / "docs").write_text("personal file at a directory path\n")
        self.assert_rejected_without_writes(root, "")


if __name__ == "__main__":
    unittest.main()
