"""S02: reviewed fixed choices and a full local A/learn/B/feedback interaction."""
import html
import json
from pathlib import Path
import re
import tempfile
import unittest
from datetime import datetime
from fastapi.testclient import TestClient
from app import db
from app.config import Settings
from app.main import create_app
from app.legacy import load_bank, response
from app.questions import BANK_VERSION, CURRENT_BANKS, bank_for_lesson, bank_snapshot

ROOT = Path(__file__).resolve().parents[2]
# Derived by solving the items, not by reading answer fields during submission.
CHOICES = {'a': ('2', '3', '1', '0', '2'), 'b': ('3', '1', '0', '2', '1')}


def csrf(text):
    return html.unescape(re.search(r'name="csrf_token" value="([^"]+)"', text).group(1))


class S02Walkthrough(unittest.TestCase):
    def test_source_pairing_and_reviewed_choices(self):
        bank = bank_for_lesson('S02')
        path = ROOT/'course-instructor/lessons/S02/questions.json'
        if path.is_file():
            source = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(source['questions'], bank.questions)
            self.assertEqual(source['concepts'], bank.concepts)
            self.assertEqual(source['content_version'], 's02-focused-review-2026-09-20')
        self.assertEqual(BANK_VERSION, 'ml-v15-s03-terminology-2026-09-22')
        self.assertEqual(bank.durations, {'attempt_a': 240, 'learn': 300, 'attempt_b': 240})
        for phase, choices in CHOICES.items():
            for i, choice in enumerate(choices, 1):
                q = bank.question(f'S02-{i:02}', phase)
                self.assertEqual(q['answer'], choice)
                self.assertEqual(q['id'], f'S02-{phase.upper()}-{i:02}')
                self.assertLess(len(q['prompt']), 180)
                self.assertNotIn(q['prompt'], bank.item(f'S02-{i:02}')['tutor_context'])
                self.assertTrue(q['explanation'])

    def test_public_reads_still_omit_answers(self):
        status, public = response('/ml-check/api/lessons/S02', load_bank())
        self.assertEqual(status, 200)
        for q in public['questions']:
            self.assertEqual(set(q), {'id', 'phase', 'prompt', 'options'})

    def test_shared_feedback_renders_unanswered_a_and_b_for_all_lessons(self):
        with tempfile.TemporaryDirectory() as temp:
            path = str(Path(temp)/'feedback.sqlite3')
            settings = Settings(database_path=path, session_secret='local-feedback-only',
                                gitea_base_url='https://example.invalid', gitea_client_id='', gitea_client_secret='',
                                public_base_url='http://testserver/ml-check', teacher_logins=frozenset(),
                                secure_cookie=False, testing=True)
            with TestClient(create_app(settings)) as client:
                client.get('/ml-check/test-login?login=feedback_learner&role=student')
                for bank in CURRENT_BANKS:
                    with self.subTest(lesson=bank.lesson_id):
                        session = db.create_session(
                            path,
                            bank.lesson_id,
                            bank.title,
                            BANK_VERSION,
                            bank_snapshot(bank),
                        )
                        db.set_phase(path, session['id'], 'result', None)
                        response = client.get('/ml-check/current')
                        self.assertEqual(response.status_code, 200)
                        text = html.unescape(response.text)
                        self.assertEqual(text.count('你的选择：未作答'), 10)
                        for q in bank.questions:
                            self.assertIn(q['prompt'], text)
                            self.assertIn(q['explanation'], text)

    def test_full_interaction_including_an_error_and_both_feedback_explanations(self):
        with tempfile.TemporaryDirectory() as temp:
            path = str(Path(temp)/'s02.sqlite3')
            settings = Settings(database_path=path, session_secret='local-s02-review-only',
                                gitea_base_url='https://example.invalid', gitea_client_id='', gitea_client_secret='',
                                public_base_url='http://testserver/ml-check', teacher_logins=frozenset(),
                                secure_cookie=False, testing=True)
            app = create_app(settings)
            with TestClient(app) as teacher, TestClient(app) as student:
                teacher.get('/ml-check/test-login?login=teacher_s02&role=teacher')
                page = teacher.get('/ml-check/teacher')
                r = teacher.post('/ml-check/teacher/session', data={'csrf_token': csrf(page.text), 'lesson_id': 'S02'}, follow_redirects=False)
                self.assertEqual(r.status_code, 303)
                session = db.current_session(path); sid = session['id']
                student.get('/ml-check/test-login?login=student_s02&role=student')
                bank = bank_for_lesson('S02')
                def phase(value):
                    token = csrf(teacher.get('/ml-check/teacher').text)
                    result = teacher.post('/ml-check/teacher/phase', data={'csrf_token': token, 'session_id': sid, 'phase': value}, follow_redirects=False)
                    self.assertEqual(result.status_code, 303)
                    if value != 'result':
                        current = db.get_session(path, sid)
                        seconds = (datetime.fromisoformat(current['phase_ends_at'])-datetime.fromisoformat(current['phase_started_at'])).total_seconds()
                        self.assertEqual(seconds, 300 if value == 'learn' else 240)
                for value in ('a', 'learn', 'b'):
                    phase(value)
                    if value == 'learn':
                        page = student.get('/ml-check/current')
                        for item in bank.items:
                            self.assertIn(item['title'], html.unescape(page.text))
                            for p in ('a', 'b'):
                                self.assertNotIn(item['pair'][p]['prompt'], html.unescape(page.text))
                        result = student.post('/ml-check/learn/complete', data={'csrf_token': csrf(page.text), 'session_id': sid}, follow_redirects=False)
                        self.assertEqual(result.status_code, 303)
                        self.assertIn('学习阶段已完成', student.get('/ml-check/current').text)
                        continue
                    for i, selected in enumerate(CHOICES[value], 1):
                        page = student.get('/ml-check/current'); text = html.unescape(page.text)
                        q = bank.question(f'S02-{i:02}', value)
                        self.assertIn(q['prompt'], text)
                        self.assertNotIn(q['explanation'], text)
                        self.assertNotIn('参考选项：', text)
                        # Include one deliberate A error to exercise the need to review A, not just B.
                        actual_choice = '0' if value == 'a' and i == 2 else selected
                        payload = dict(csrf_token=csrf(page.text), session_id=sid, concept_id=f'S02-{i:02}',
                                       phase=value, option_id=actual_choice, confidence='unsure')
                        wrong_phase = dict(payload, phase='b' if value == 'a' else 'a')
                        self.assertEqual(student.post('/ml-check/answer', data=wrong_phase).status_code, 409)
                        result = student.post('/ml-check/answer', data=payload, follow_redirects=False)
                        self.assertEqual(result.status_code, 303)
                        self.assertEqual(student.post('/ml-check/answer', data=payload).status_code, 409)
                    self.assertIn('已完成', student.get('/ml-check/current').text)
                with db.connect(path) as connection:
                    stored = connection.execute('SELECT phase, COUNT(*) n, SUM(correct) correct FROM responses WHERE session_id=? GROUP BY phase', (sid,)).fetchall()
                    self.assertEqual([(r['phase'], r['n'], r['correct']) for r in stored], [('a', 5, 4), ('b', 5, 5)])
                    self.assertEqual(connection.execute('SELECT COUNT(*) FROM learning_completions WHERE session_id=?', (sid,)).fetchone()[0], 1)
                phase('result')
                text = html.unescape(student.get('/ml-check/current').text)
                for q in bank.questions:
                    self.assertIn(q['prompt'], text)
                    self.assertIn(q['explanation'], text)
                self.assertIn('A：需复习', text)
                self.assertIn('B：正确', text)
                self.assertIn('你的选择：', text)
                self.assertIn('参考选项：', text)
                self.assertEqual(student.get('/ml-check/teacher').status_code, 403)
                for q in student.get('/ml-check/api/lessons/S02').json()['questions']:
                    self.assertEqual(set(q), {'id', 'phase', 'prompt', 'options'})
                exported = teacher.get('/ml-check/teacher/export.csv').text
                self.assertIn('student_s02,student_s02,5,4,1,5,5', exported)


if __name__ == '__main__':
    unittest.main()
