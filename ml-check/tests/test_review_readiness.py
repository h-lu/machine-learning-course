"""S07 配对题和公开入口的回归检查；题意仍须人工审核。"""
import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.questions import BANK_VERSION, bank_for_lesson
from app.legacy import load_bank, response
from ml_check.checker import Report, check_prose

ROOT = Path(__file__).resolve().parents[2]


class ReviewReadiness(unittest.TestCase):
    def test_s07_source_and_published_bank_match(self):
        path = ROOT / 'course-instructor/lessons/S07/questions.json'
        if not path.is_file():
            self.skipTest('独立服务包不含教师源文件')
        source = json.loads(path.read_text(encoding='utf-8'))
        bank = bank_for_lesson('S07')
        self.assertEqual(bank.questions, source['questions'])
        self.assertEqual(bank.concepts, source['concepts'])
        self.assertEqual(source['content_version'], 's07-learning-representation-2026-09-21')
        self.assertEqual(BANK_VERSION, 'ml-v15-s03-terminology-2026-09-22')

    def test_s07_pairs_remain_bound_to_the_same_concept(self):
        bank = bank_for_lesson('S07')
        self.assertEqual(len(bank.concepts), 5)
        self.assertEqual(len(bank.questions), 10)
        for i, item in enumerate(bank.items, 1):
            self.assertEqual(item['concept_id'], f'S07-{i:02}')
            self.assertNotEqual(item['pair']['a']['prompt'], item['pair']['b']['prompt'])
            for phase in ('a', 'b'):
                question = bank.question(item['concept_id'], phase)
                self.assertEqual(question['id'], f'S07-{phase.upper()}-{i:02}')
                self.assertEqual(question['concept_id'], item['concept_id'])
                self.assertNotIn(item['pair'][phase]['prompt'], item['tutor_context'])

    def test_s07_does_not_copy_correct_options_into_prompts(self):
        # This catches literal answer echoing, not every possible semantic hint.
        for q in bank_for_lesson('S07').questions:
            with self.subTest(question=q['id']):
                self.assertNotIn(q['options'][q['answer']], q['prompt'])
                self.assertNotIn('先读清楚这个场景', q['prompt'])
                self.assertNotIn('先看一个实际学习场景', q['prompt'])
                self.assertLess(len(q['prompt']), 180)
                self.assertTrue(q['explanation'].strip())

    def test_s07_timer_uses_the_course_wide_four_five_four_schedule(self):
        self.assertEqual(bank_for_lesson('S07').durations,
                         {'attempt_a': 240, 'learn': 300, 'attempt_b': 240})

    def test_s07_public_interfaces_keep_answers_private(self):
        raw = load_bank()
        status, payload = response('/ml-check/api/lessons/S07', raw)
        self.assertEqual(status, 200)
        for q in payload['questions']:
            self.assertEqual(set(q), {'id', 'phase', 'prompt', 'options'})
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(database_path=str(Path(tmp) / 'test.sqlite3'),
                                session_secret='local-review-test-only',
                                gitea_base_url='https://example.invalid',
                                gitea_client_id='', gitea_client_secret='',
                                public_base_url='http://testserver/ml-check',
                                teacher_logins=frozenset(), secure_cookie=False, testing=True)
            with TestClient(create_app(settings)) as client:
                result = client.get('/ml-check/api/lessons/S07')
                self.assertEqual(result.status_code, 200)
                self.assertEqual(client.get('/ml-check/healthz').json()['bank_version'], BANK_VERSION)
                self.assertEqual(len(result.json()['questions']), 10)
                for q in result.json()['questions']:
                    self.assertEqual(set(q), {'id', 'phase', 'prompt', 'options'})

    def test_current_navigation_has_no_missing_local_targets(self):
        if not (ROOT / 'AGENTS.md').is_file():
            self.skipTest('独立服务包不含完整课程入口')
        report = Report(ROOT, 'navigation')
        for relative in ('README.md', 'course-instructor/RELEASE.md',
                         'course-student-template/docs/KNOWLEDGE_CHECK.md',
                         'course-student-template/docs/SUBMISSION.md'):
            check_prose(ROOT / relative, report)
        self.assertFalse(report.failed(True), report.issues)

    def test_student_handoff_uses_account_based_completion(self):
        root = ROOT / 'course-student-template'
        if not root.is_dir():
            self.skipTest('独立服务包不含学生说明')
        for name in ('KNOWLEDGE_CHECK.md', 'SUBMISSION.md'):
            text = (root / 'docs' / name).read_text(encoding='utf-8')
            self.assertIn('Gitea', text)
            self.assertNotIn('保存匿名完成凭据链接', text)
            self.assertNotIn('系统返回匿名完成凭据', text)


if __name__ == '__main__':
    unittest.main()
