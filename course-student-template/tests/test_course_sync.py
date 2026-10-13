"""Missing lesson09 sync preserves homework and custom activation metadata."""
import importlib.util
import hashlib
import os
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('course_sync_test_target', ROOT/'scripts/course.py')
course = importlib.util.module_from_spec(spec)
spec.loader.exec_module(course)
spec10 = importlib.util.spec_from_file_location('course_l10_sync_test_target', ROOT/'scripts/course_l10.py')
course10 = importlib.util.module_from_spec(spec10)
spec10.loader.exec_module(course10)


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

class Lesson10SyncTests(unittest.TestCase):
    def setUp(self):
        MissingLessonSyncTests.setUp(self)
        content = {
            'lesson-10/README.md': 'lesson10 release',
            'lesson-10/analysis.py': "from pathlib import Path\np=Path('lesson-10/artifacts/probe.txt');p.parent.mkdir(parents=True,exist_ok=True);p.write_text('probe')\n",
            'lesson-10/report.md': 'technical fixture report',
            'lesson-10/submission.json': json.dumps({'lesson': 'lesson-10', 'status': 'not_started', 'report': 'lesson-10/report.md', 'artifacts': ['lesson-10/artifacts/probe.txt'], 'run': ['python3', 'lesson-10/analysis.py']}),
            'scripts/course_l10.py': (ROOT/'scripts/course_l10.py').read_text(),
            'mlcourse/__init__.py': '',
            'mlcourse/sms_course.py': 'manual-only compatible support',
            'data/sms/train.csv': 'id,label,text,text_sha256,group_id,split\ntrain-1,ham,fixture,hash,g1,train\n',
            'data/sms/dev.csv': 'id,label,text,text_sha256,group_id,split\ndev-1,spam,fixture,hash,g2,dev\n',
            'data/sms/split_manifest.csv': 'id,text_sha256,group_id,split\ntrain-1,hash,g1,train\ndev-1,hash,g2,dev\n',
            'data/sms/DATA.md': 'technical source fixture',
            'data/sms/cache/dev.npy': 'must not copy',
            'data/sms/encoder/model.onnx': 'must not copy',
            'data/sms/original-readme.txt': 'must not copy labelled upstream examples',
            'lesson-11/README.md': 'must not copy later lesson',
        }
        metadata = {'student_package': {'scope': 'train/dev fixture'}, 'file_sha256': {
            'course-student-template/' + name: hashlib.sha256(value.encode()).hexdigest()
            for name, value in content.items() if name in {
                'data/sms/train.csv', 'data/sms/dev.csv', 'data/sms/split_manifest.csv'
            }
        }}
        content['data/sms/provenance.json'] = json.dumps(metadata)
        for name, value in content.items():
            p = self.remote/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(value)
        git(self.remote, 'add', '.'); git(self.remote, 'commit', '-m', 'lesson10 fixture')
        # Simulated personal edits to every old lesson and the existing script.
        for number in range(1, 10):
            for name in ['README.md', 'analysis.py', 'report.md', 'artifacts/my-result.csv']:
                p = self.root/f'lesson-{number:02d}'/name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(f'personal lesson {number} file {name}\n')
        p = self.root/'scripts/course.py'; p.parent.mkdir(); p.write_text('personal workflow edits')

    def snapshot(self):
        return MissingLessonSyncTests.snapshot(self)

    def test_two_syncs_preserve_all_old_bytes_and_only_add_lesson10(self):
        before = self.snapshot(); course10.sync(self.root)
        for name, value in before.items():
            if name != 'active_lessons.json': self.assertEqual((self.root/name).read_bytes(), value)
        expected = dict(self.config, active_student_lessons=['lesson-07', 'lesson-01', 'lesson-10'])
        self.assertEqual(json.loads((self.root/'active_lessons.json').read_text()), expected)
        self.assertTrue((self.root/'lesson-10/analysis.py').exists())
        self.assertTrue((self.root/'mlcourse/sms_course.py').exists())
        for name in ['lesson-11', 'data/sms/cache', 'data/sms/encoder', 'data/sms/original-readme.txt', 'mlcourse/future.py']:
            self.assertFalse((self.root/name).exists(), name)
        after = self.snapshot(); course10.sync(self.root)
        self.assertEqual(self.snapshot(), after)

    def test_existing_lesson10_is_skipped_as_a_whole(self):
        lesson = self.root/'lesson-10'; lesson.mkdir(); (lesson/'report.md').write_text('personal unfinished lesson10')
        course10.sync(self.root)
        self.assertEqual((lesson/'report.md').read_text(), 'personal unfinished lesson10')
        self.assertFalse((lesson/'README.md').exists())
        self.assertTrue((self.root/'mlcourse/sms_course.py').exists())

    def test_independent_cli_updates_old_course_script_without_replacing_it(self):
        old = subprocess.check_output(['git', '-C', str(ROOT.parent), 'show', '6f97c4ff0547adc70d7e56cbecb827c3c0fa6174:course-student-template/scripts/course.py'])
        (self.root/'scripts/course.py').write_bytes(old)
        before = self.snapshot()
        bootstrap = """set -e
git fetch "$LESSON10_RELEASE_URL" main
lesson10_tmp=$(mktemp)
trap 'rm -f "$lesson10_tmp"' EXIT
git show FETCH_HEAD:scripts/course_l10.py > "$lesson10_tmp"
python3 "$lesson10_tmp" sync --destination "$PWD"
"""
        subprocess.run(['bash', '-c', bootstrap], cwd=self.root,
                       env=dict(os.environ, LESSON10_RELEASE_URL=str(self.remote)),
                       check=True, capture_output=True)
        for name, value in before.items():
            if name != 'active_lessons.json': self.assertEqual((self.root/name).read_bytes(), value)
        first = self.snapshot()
        subprocess.run(['python3', str(self.root/'scripts/course_l10.py'), 'sync'], check=True, capture_output=True)
        self.assertEqual(self.snapshot(), first)
        self.assertEqual((self.root/'scripts/course.py').read_bytes(), old)
        # The untouched old run/check CLI already accepts lesson10 from its manifest.
        subprocess.run(['python3', 'scripts/course.py', 'run', '10'], cwd=self.root, check=True, capture_output=True)
        sub_path = self.root/'lesson-10/submission.json'; sub = json.loads(sub_path.read_text())
        sub['status'] = 'complete'; sub_path.write_text(json.dumps(sub))
        subprocess.run(['python3', 'scripts/course.py', 'check', '10'], cwd=self.root, check=True, capture_output=True)
        self.assertEqual((self.root/'scripts/course.py').read_bytes(), old)

    def test_different_shared_code_fails_before_adding_content(self):
        (self.root/'mlcourse/sms_course.py').write_text('personal incompatible module')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, '共享代码.*无法确认兼容'):
            course10.sync(self.root)
        self.assertEqual(self.snapshot(), before)

    def test_different_data_fails_before_adding_content(self):
        p = self.root/'data/sms/train.csv'; p.parent.mkdir(parents=True); p.write_text('personal data')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, '数据与发布字节不同'):
            course10.sync(self.root)
        self.assertEqual(self.snapshot(), before)

    def test_malformed_or_incompatible_local_metadata_is_preserved(self):
        p = self.root/'data/sms/provenance.json'; p.parent.mkdir(parents=True)
        for value in [{}, {'file_sha256': {}}]:
            p.write_text(json.dumps(value)); before = self.snapshot()
            with self.assertRaises(ValueError): course10.sync(self.root)
            self.assertEqual(self.snapshot(), before)

    def test_compatible_custom_metadata_and_data_notice_are_not_overwritten(self):
        p = self.root/'data/sms/provenance.json'; p.parent.mkdir(parents=True)
        meta = json.loads((self.remote/'data/sms/provenance.json').read_text()); meta['custom'] = ['keep']
        p.write_text(json.dumps(meta, indent=4))
        (p.parent/'DATA.md').write_text('personal technical notes')
        before = self.snapshot(); course10.sync(self.root)
        for name, value in before.items():
            if name != 'active_lessons.json': self.assertEqual((self.root/name).read_bytes(), value)

    def test_bad_release_hash_fails_before_any_files_are_added(self):
        p = self.remote/'data/sms/provenance.json'; meta = json.loads(p.read_text())
        meta['file_sha256']['course-student-template/data/sms/train.csv'] = 'wrong'
        p.write_text(json.dumps(meta)); git(self.remote, 'add', '.'); git(self.remote, 'commit', '-m', 'bad fixture hash')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, '数据哈希与来源清单不符'):
            course10.sync(self.root)
        self.assertEqual(self.snapshot(), before)

    def test_missing_release_dependency_fails_before_adding_lesson(self):
        git(self.remote, 'rm', 'data/sms/DATA.md'); git(self.remote, 'commit', '-m', 'missing fixture dependency')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, '支持文件不完整'):
            course10.sync(self.root)
        self.assertEqual(self.snapshot(), before)

    def test_existing_parent_file_fails_without_partial_additions(self):
        (self.root/'data').write_text('personal file at directory path')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, '上级路径不是目录'):
            course10.sync(self.root)
        self.assertEqual(self.snapshot(), before)

    def test_external_parent_symlink_fails_without_touching_target(self):
        outside = Path(self.temp.name)/'outside'; outside.mkdir(); (outside/'keep').write_text('outside bytes')
        (self.root/'data').symlink_to(outside, target_is_directory=True)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, '路径超出仓库'):
            course10.sync(self.root)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual((outside/'keep').read_text(), 'outside bytes')
        self.assertEqual(sorted(p.name for p in outside.iterdir()), ['keep'])


if __name__ == '__main__': unittest.main()
