"""Missing lesson09 sync preserves homework and custom activation metadata."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('course_sync_test_target', ROOT/'scripts/course.py')
course = importlib.util.module_from_spec(spec)
spec.loader.exec_module(course)


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL)


class MissingLessonSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.remote = Path(self.temp.name)/'release'
        self.root = Path(self.temp.name)/'student'
        for p in [self.remote, self.root]:
            p.mkdir(); git(p, 'init', '-b', 'main')
            git(p, 'config', 'user.name', 'Test'); git(p, 'config', 'user.email', 'test@example.invalid')
        for name, content in {
            'lesson-09/README.md': 'new lesson', 'lesson-09/analysis.py': 'new starter',
            'mlcourse/bike_models09.py': 'new model', 'mlcourse/lesson_io.py': 'new IO',
            'lesson-08/report.md': 'must not replace', 'lesson-10/README.md': 'future',
            'mlcourse/future.py': 'not a lesson09 dependency',
        }.items():
            p = self.remote/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content)
        git(self.remote, 'add', '.'); git(self.remote, 'commit', '-m', 'fixture')
        git(self.root, 'remote', 'add', 'course-release', str(self.remote))
        self.config = {'active_student_lessons': ['lesson-07', 'lesson-01'], 'custom': {'keep': [3, 2, 1]}, 'active_instructor_lessons': ['S05']}
        (self.root/'active_lessons.json').write_text(json.dumps(self.config))
        (self.root/'lesson-08').mkdir(); (self.root/'lesson-08/report.md').write_text('student unpublished work')
        (self.root/'mlcourse').mkdir(); (self.root/'mlcourse/lesson_io.py').write_text('student shared-file changes')

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file() and '.git' not in p.relative_to(self.root).parts}

    def test_missing_lesson_and_only_required_missing_files(self):
        before = self.snapshot(); course.sync(self.root)
        for name, value in before.items():
            if name != 'active_lessons.json': self.assertEqual((self.root/name).read_bytes(), value)
        expected = dict(self.config, active_student_lessons=['lesson-07', 'lesson-01', 'lesson-09'])
        self.assertEqual(json.loads((self.root/'active_lessons.json').read_text()), expected)
        self.assertTrue((self.root/'lesson-09/analysis.py').exists())
        self.assertTrue((self.root/'mlcourse/bike_models09.py').exists())
        self.assertFalse((self.root/'lesson-10').exists())
        self.assertFalse((self.root/'mlcourse/future.py').exists())
        after = self.snapshot(); course.sync(self.root); self.assertEqual(self.snapshot(), after)

    def test_existing_entire_lesson_is_skipped_even_if_incomplete(self):
        (self.root/'lesson-09').mkdir(); (self.root/'lesson-09/report.md').write_text('my existing work')
        course.sync(self.root)
        self.assertEqual((self.root/'lesson-09/report.md').read_text(), 'my existing work')
        self.assertFalse((self.root/'lesson-09/README.md').exists())

    def test_existing_registration_preserves_manifest_bytes(self):
        self.config['active_student_lessons'].append('lesson-09')
        manifest = self.root/'active_lessons.json'; manifest.write_text(json.dumps(self.config, indent=4))
        before = manifest.read_bytes(); course.sync(self.root)
        self.assertEqual(manifest.read_bytes(), before)

    def test_invalid_activation_list_fails_before_adding_content(self):
        (self.root/'active_lessons.json').write_text('{"active_student_lessons": []}')
        before = self.snapshot()
        with self.assertRaises(ValueError): course.sync(self.root)
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__': unittest.main()
