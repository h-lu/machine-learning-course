"""问题与评价模块：源题、术语对应、计时与公开接口。"""
from pathlib import Path
import json
import tempfile
import unittest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from app import db
from app.config import Settings
from app.main import create_app
from app.legacy import load_bank, response
from app.questions import BANK_VERSION, bank_for_lesson

ROOT = Path(__file__).resolve().parents[2]
IDS = [f'S{i:02}' for i in range(1,7)]


class FoundationBank(unittest.TestCase):
    def test_source_questions_and_durations_are_synchronized(self):
        if not (ROOT/'course-instructor').exists():
            self.skipTest('独立服务包没有教师源文件')
        for lesson in IDS:
            source = json.loads((ROOT/f'course-instructor/lessons/{lesson}/questions.json').read_text())
            bank = bank_for_lesson(lesson)
            self.assertEqual(bank.title, source['title'])
            self.assertEqual(bank.questions, source['questions'])
            self.assertEqual(bank.concepts, source['concepts'])
            self.assertEqual(bank.durations, source['durations'])
            expected_version = ('s01-focused-review-2026-09-19' if lesson == 'S01' else 's02-focused-review-2026-09-20' if lesson == 'S02' else 'foundations-2026-09-19')
            self.assertEqual(source['content_version'], expected_version)

    def test_five_concepts_have_one_a_and_one_distinct_b(self):
        prompts=[]
        for lesson in IDS:
            bank=bank_for_lesson(lesson)
            self.assertEqual(bank.concept_ids, [f'{lesson}-{i:02}' for i in range(1,6)])
            for item in bank.items:
                self.assertNotEqual(item['pair']['a']['prompt'],item['pair']['b']['prompt'])
                for phase in ('a','b'):
                    q=item['pair'][phase]
                    self.assertEqual(q['concept_id'],item['concept_id'])
                    self.assertNotIn(q['prompt'],item['tutor_context'])
                    self.assertEqual(len(q['options']),4)
                    self.assertIs(type(q['answer']),int)
                    self.assertIn(q['answer'],range(4))
                    self.assertGreaterEqual(len(q['prompt']),25)
                    self.assertTrue(q['explanation'].strip())
                    prompts.append(q['prompt'])
        self.assertEqual(len(prompts),60)
        self.assertEqual(len(set(prompts)),60)

    def test_legacy_public_endpoint_does_not_expose_answers(self):
        raw=load_bank()
        self.assertEqual(raw['version'],BANK_VERSION)
        for lesson in IDS:
            status,payload=response('/ml-check/api/lessons/'+lesson,raw)
            self.assertEqual(status,200)
            self.assertEqual(payload['title'],bank_for_lesson(lesson).title)
            self.assertEqual(len(payload['questions']),10)
            for q in payload['questions']:
                self.assertEqual(set(q),{'id','phase','prompt','options'})

    def test_fastapi_public_routes_report_the_candidate_bank(self):
        with tempfile.TemporaryDirectory() as temp:
            settings=Settings(database_path=str(Path(temp)/'test.sqlite3'),session_secret='only-for-local-tests',
                gitea_base_url='https://example.invalid',gitea_client_id='',gitea_client_secret='',
                public_base_url='http://testserver/ml-check',teacher_logins=frozenset(),secure_cookie=False,testing=True)
            with TestClient(create_app(settings)) as client:
                self.assertEqual(client.get('/ml-check/healthz').json()['bank_version'],BANK_VERSION)
                for lesson in IDS:
                    result=client.get('/ml-check/api/lessons/'+lesson)
                    self.assertEqual(result.status_code,200)
                    self.assertEqual(result.json()['title'],bank_for_lesson(lesson).title)
                    for q in result.json()['questions']:
                        self.assertEqual(set(q),{'id','phase','prompt','options'})

    def test_stage_durations_leave_two_minutes_for_submission(self):
        with tempfile.TemporaryDirectory() as temp:
            path=str(Path(temp)/'test.sqlite3')
            db.initialize(path,'S01','阶段测试')
            session=db.current_session(path)
            for lesson in IDS:
                durations=bank_for_lesson(lesson).durations
                self.assertEqual(sum(durations.values())+120,900)
                for phase,key in [('a','attempt_a'),('learn','learn'),('b','attempt_b')]:
                    db.set_phase(path,session['id'],phase,durations[key])
                    current=db.get_session(path,session['id'])
                    elapsed=datetime.fromisoformat(current['phase_ends_at'])-datetime.fromisoformat(current['phase_started_at'])
                    self.assertEqual(elapsed,timedelta(seconds=durations[key]))

if __name__=='__main__':
    unittest.main()
