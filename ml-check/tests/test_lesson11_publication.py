"""L11 formal registration is exact and scoped; production retains full32."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from app.questions import BANK_VERSION, CURRENT_BANKS, bank_for_lesson
from ml_check.checker import active_ids, formal_question_numbers

ROOT = Path(__file__).resolve().parents[2]
INSTRUCTOR = ROOT / 'course-instructor'
BANKS = ROOT / 'ml-check/deploy/banks'
VERSION = 'ml-lesson11-sms-20261018-v1'
SHA = '2026dd01e062258e88aa44d8bff83676fe0332d14838d9970649a6d242951706'


def read(path): return json.loads(path.read_text())


class Lesson11Publication(unittest.TestCase):
    def test_approved_source_and_runtime_fields_are_exact(self):
        p = INSTRUCTOR / 'lessons/S09/questions.json'
        self.assertEqual(p.read_bytes(), p.with_name('questions.draft-20261018.json').read_bytes())
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), SHA)
        source = read(p); bank = bank_for_lesson('S09')
        for key in ['title', 'questions', 'concepts', 'durations']:
            self.assertEqual(getattr(bank, key), source[key])
        self.assertEqual(BANK_VERSION, VERSION)
        self.assertEqual(len(CURRENT_BANKS), 11)
        self.assertEqual(bank.concept_ids, [f'S09-{i}' for i in range(21, 26)])
        self.assertEqual([q['answer'] for q in bank._by_phase('A')], [1, 0, 3, 1, 3])
        self.assertEqual([q['answer'] for q in bank._by_phase('B')], [2, 1, 2, 0, 2])

    def test_formal_number_registration_is_exact_not_general_relaxation(self):
        active = active_ids(INSTRUCTOR, 'instructor')
        self.assertEqual(formal_question_numbers(INSTRUCTOR, active), {'S08':[11,12,13,14,15], 'S09':[21,22,23,24,25]})
        with tempfile.TemporaryDirectory() as temporary:
            p = Path(temporary)
            for invalid in [{'S07':[21,22,23,24,25]}, {'S09':[11,12,13,14,15]}, {'S09':[21,22,23,24,True]}]:
                (p/'active_lessons.json').write_text(json.dumps({'formal_question_numbers':invalid}))
                with self.assertRaises(ValueError): formal_question_numbers(p, active)
            (p/'active_lessons.json').write_text(json.dumps({'formal_question_numbers':{'S09':[21,22,23,24,25]}}))
            with self.assertRaises(ValueError): formal_question_numbers(p, ['S08'])

    def test_full_production_bank_changes_only_S09_and_old_archive_bytes_survive(self):
        previous = BANKS/'archive/ml-lesson10-sms-20261013-v1.lessons.json'
        self.assertEqual(hashlib.sha256(previous.read_bytes()).hexdigest(), '7786ade4caf576e671e13398a999b44ccdeded64e777cbfc368e3dfe407ecd79')
        old = read(previous); current = read(BANKS/'lessons-lesson11-20261018.json')
        self.assertEqual(len(current['lessons']), 32)
        self.assertEqual(current['version'], VERSION)
        self.assertEqual([a['lesson_id'] for a,b in zip(old['lessons'],current['lessons']) if a!=b], ['S09'])
        self.assertEqual(read(BANKS/'archive/ml-lesson10-sms-20261013-v1.S09.json'), next(x for x in old['lessons'] if x['lesson_id']=='S09'))
        before = read(ROOT/'ml-check/deploy/lesson11-20261018/archive/local-lesson10-bank.json')
        local = read(ROOT/'ml-check/app/question_bank/lessons.json')
        self.assertEqual(local['lessons'][:10], before['lessons'])
        self.assertEqual(local['lessons'][-1]['lesson_id'], 'S09')
        manifest = read(BANKS/'lesson11-release-manifest.json')
        for relative, sha in manifest['files'].items():
            self.assertEqual(hashlib.sha256((BANKS/relative).read_bytes()).hexdigest(), sha)


if __name__=='__main__': unittest.main()
