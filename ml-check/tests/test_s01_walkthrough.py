"""只在临时数据库中模拟第三课作答；不用生产账号，不代表真人学习实验。"""
from __future__ import annotations
import html
import json
from pathlib import Path
import re
import tempfile
import unittest
from fastapi.testclient import TestClient
from app import db
from app.config import Settings
from app.main import create_app
from app.questions import BANK_VERSION, bank_for_lesson, bank_snapshot
from app.legacy import load_bank, response

ROOT = Path(__file__).resolve().parents[2]
# Reviewed choices are fixed here, not copied at run time from the answer key.
# This is a regression fixture, not an independent student or blinded reading study.
RESPONSES = {'a': [1, 0, 1, 2, 1], 'b': [2, 3, 0, 0, 3]}


def csrf(page):
    return re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)


class S01QuestionWalkthrough(unittest.TestCase):
    def test_source_concepts_keys_and_timer_match_reviewed_reading(self):
        bank = bank_for_lesson('S01')
        self.assertEqual(bank.durations, {'attempt_a': 240, 'learn': 300, 'attempt_b': 240})
        self.assertEqual(BANK_VERSION, 'ml-v13-course-map-2026-09-21')
        for i, item in enumerate(bank.items):
            for phase in ('a', 'b'):
                q = item['pair'][phase]
                self.assertEqual(q['answer'], RESPONSES[phase][i])
                self.assertEqual(q['concept_id'], f'S01-{i+1:02}')
                self.assertEqual(len(set(q['options'])), 4)
                self.assertNotIn(q['options'][q['answer']], q['prompt'])
                self.assertNotIn(q['prompt'], item['tutor_context'])
        path = ROOT/'course-instructor/lessons/S01/questions.json'
        if path.exists():
            source = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(source['content_version'], 's01-focused-review-2026-09-19')
            self.assertEqual(source['questions'], bank.questions)
            self.assertEqual(source['concepts'], bank.concepts)

    def test_student_reads_answers_learns_and_finishes_b_in_local_app(self):
        bank = bank_for_lesson('S01')
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp)/'s01.sqlite3')
            settings = Settings(database_path=path, session_secret='local-s01-test-only',
                gitea_base_url='https://example.invalid', gitea_client_id='', gitea_client_secret='',
                public_base_url='http://testserver/ml-check', teacher_logins=frozenset(),
                secure_cookie=False, testing=True)
            app = create_app(settings)
            with TestClient(app) as teacher, TestClient(app) as student:
                teacher.get('/ml-check/test-login?login=teacher-local&role=teacher')
                student.get('/ml-check/test-login?login=student-local&role=student')
                session = db.create_session(
                    path, 'S01', bank.title, BANK_VERSION, bank_snapshot(bank)
                )
                def phase(value):
                    page = teacher.get('/ml-check/teacher').text
                    r = teacher.post('/ml-check/teacher/phase', data={
                        'csrf_token': csrf(page), 'session_id': session['id'], 'phase': value},
                        follow_redirects=False)
                    self.assertEqual(r.status_code, 303)
                for part in ('a', 'b'):
                    phase(part)
                    for i, index in enumerate(RESPONSES[part]):
                        page = student.get('/ml-check/current')
                        self.assertEqual(page.status_code, 200)
                        q = bank.question(f'S01-{i+1:02}', part)
                        self.assertIn(q['prompt'], html.unescape(page.text))
                        self.assertNotIn(q['explanation'], html.unescape(page.text))
                        for option in q['options']:
                            self.assertIn(option['text'], html.unescape(page.text))
                        form = dict(csrf_token=csrf(page.text), session_id=session['id'],
                            concept_id=f'S01-{i+1:02}', phase=part, option_id=str(index), confidence='sure')
                        r = student.post('/ml-check/answer', data=form, follow_redirects=False)
                        self.assertEqual(r.status_code, 303)
                    self.assertRegex(student.get('/ml-check/current').text, rf'{part.upper()} 版[^<]*已完成')
                    if part == 'a':
                        # A submission is not accepted in the learning phase.
                        phase('learn')
                        page = student.get('/ml-check/current')
                        for q in bank.questions:
                            self.assertNotIn(q['prompt'], html.unescape(page.text))
                        self.assertIn('复制', page.text)
                        self.assertEqual(student.post('/ml-check/answer', data=form).status_code, 409)
                        r = student.post('/ml-check/learn/complete', data={
                            'csrf_token': csrf(page.text), 'session_id': session['id']}, follow_redirects=False)
                        self.assertEqual(r.status_code, 303)
                phase('result')
                page = student.get('/ml-check/current')
                self.assertEqual(page.status_code, 200)
                self.assertEqual(page.text.count('A：正确'), 5)
                self.assertEqual(page.text.count('B：正确'), 5)
                for item in bank.items:
                    self.assertIn(item['pair']['b']['explanation'], html.unescape(page.text))
                rows = db.export_rows(path, session['id'])
                self.assertEqual(len(rows), 1)  # export aggregates one row per student
                self.assertEqual(tuple(rows[0][k] for k in
                                       ('a_count', 'a_correct', 'b_count', 'b_correct', 'learned')),
                                 (5, 5, 5, 5, 1))

    def test_public_questions_include_no_answer_or_explanation_fields(self):
        status, payload = response('/ml-check/api/lessons/S01', load_bank())
        self.assertEqual(status, 200)
        self.assertEqual(len(payload['questions']), 10)
        for q in payload['questions']:
            self.assertEqual(set(q), {'id', 'phase', 'prompt', 'options'})

if __name__ == '__main__':
    unittest.main()
