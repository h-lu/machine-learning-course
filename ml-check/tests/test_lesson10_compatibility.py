"""Offline drafts do not activate banks or weaken legacy checks."""
import json
from pathlib import Path
import tempfile
import unittest

from ml_check.checker import Report, active_ids, check_prose, check_question_set, check_repo


def bank(lesson, numbers):
    concepts = [dict(concept_id=f'{lesson}-{n:02d}', title=f'Fixture topic {n}', tutor_context='Fixture context') for n in numbers]
    questions = [dict(id=f'{lesson}-{phase}-{n:02d}', phase=phase, concept_id=f'{lesson}-{n:02d}',
                      prompt='Fixture question?', options=['a', 'b', 'c', 'd'], answer=0, explanation='Fixture explanation')
                 for n in numbers for phase in ['A', 'B']]
    return dict(lesson_id=lesson, concepts=concepts, questions=questions)


class OfflineDraftChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'README.md').write_text('Fixture instructor root')
        self.config = dict(active_instructor_lessons=['C01'], offline_instructor_lessons={
            'S08': dict(questions='questions.draft-fixture.json', concept_numbers=[11, 12, 13, 14, 15])})
        for lesson in ['C01', 'S08']:
            p = self.root/'lessons'/lesson; p.mkdir(parents=True)
            for name in ['RUNBOOK.md', 'REFERENCE.md']: (p/name).write_text('Fixture technical material')
        (self.root/'lessons/C01/questions.json').write_text(json.dumps(bank('C01', [1, 2, 3, 4, 5])))
        (self.root/'lessons/S08/questions.draft-fixture.json').write_text(json.dumps(bank('S08', [11, 12, 13, 14, 15])))
        self.save()

    def save(self):
        (self.root/'active_lessons.json').write_text(json.dumps(self.config))

    def check(self):
        self.save(); return check_repo(self.root, 'instructor')

    def test_explicit_draft_passes_without_activating_or_writing_formal_bank(self):
        formal = self.root/'lessons/C01/questions.json'; before = formal.read_bytes()
        self.assertFalse(self.check().failed(True), self.check().issues)
        self.assertEqual(active_ids(self.root, 'instructor'), ['C01'])
        self.assertFalse((self.root/'lessons/S08/questions.json').exists())
        self.assertEqual(formal.read_bytes(), before)

    def test_unregistered_instructor_directory_still_fails(self):
        self.config.pop('offline_instructor_lessons')
        self.assertIn('lesson_set', {x['code'] for x in self.check().issues})

    def test_missing_registered_draft_fails(self):
        (self.root/'lessons/S08/questions.draft-fixture.json').unlink()
        self.assertIn('missing', {x['code'] for x in self.check().issues})

    def test_active_and_offline_overlap_is_rejected(self):
        self.config['active_instructor_lessons'].append('S08')
        self.assertIn('offline', {x['code'] for x in self.check().issues})

    def test_draft_path_cannot_escape_the_lesson(self):
        self.config['offline_instructor_lessons']['S08']['questions'] = 'questions.draft-dir/../../outside.json'
        self.assertIn('offline', {x['code'] for x in self.check().issues})

    def test_duplicate_draft_numbers_are_rejected(self):
        self.config['offline_instructor_lessons']['S08']['concept_numbers'] = [11, 12, 13, 14, 14]
        self.assertIn('offline', {x['code'] for x in self.check().issues})

    def test_formal_numbering_constraint_is_unchanged(self):
        path = self.root/'lessons/S08/questions.draft-fixture.json'; value = json.loads(path.read_text())
        formal = Report(self.root, 'instructor'); check_question_set(value, path, formal, 'S08')
        self.assertTrue(formal.failed())
        draft = Report(self.root, 'instructor'); check_question_set(value, path, draft, 'S08', [11, 12, 13, 14, 15])
        self.assertFalse(draft.failed(True), draft.issues)


class Lesson10WordingChecks(unittest.TestCase):
    def test_approved_context_is_scoped_to_lesson10(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for number in [9, 10]:
                p = root/f'lesson-{number:02d}'/'README.md'; p.parent.mkdir()
                p.write_text('概率、阈值、容量的行动规则。历史英语短信与当前中文短信的适用范围。')
                report = Report(root, 'student'); check_prose(p, report, student=True)
                self.assertEqual(report.failed(), number == 9)

    def test_missing_context_does_not_disable_wording_check(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); p = root/'lesson-10'/'README.md'; p.parent.mkdir()
            p.write_text('行动规则、适用范围、问题契约。')
            report = Report(root, 'student'); check_prose(p, report, student=True)
            self.assertEqual(len(report.issues), 3)


if __name__ == '__main__': unittest.main()
