"""在5090用生产应用代码和临时数据库走完每课A→学习→B→反馈。"""
from contextlib import nullcontext
import gc
import html
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
WORK = Path('/home/hblu/Documents/Codex/ml-expert-fix-20261104')
RUNTIME = WORK/'runtime'
RUNTIME.mkdir(exist_ok=True)
shutil.copytree('/home/hblu/Documents/Codex/ml-lesson16-quiz/runtime/app',RUNTIME/'app',dirs_exist_ok=True)
shutil.copyfile(HERE/'lessons.json',RUNTIME/'app/question_bank/lessons.json')
sys.path.insert(0,str(RUNTIME))
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app import db
from app.questions import BANK_VERSION, CURRENT_BANKS, bank_from_snapshot
assert BANK_VERSION == json.loads((HERE/'lessons.json').read_text())['version']

def csrf(text):
    return html.unescape(re.search(r'name="csrf_token" value="([^"]+)"',text).group(1))

records=[]
with nullcontext(tempfile.mkdtemp(prefix='synthetic-quiz-',dir=WORK)) as folder:
    database=str(Path(folder)/'classroom.sqlite3')
    settings=Settings(database_path=database,session_secret='synthetic-expert-review-secret',
        gitea_base_url='https://example.invalid',gitea_client_id='',gitea_client_secret='',
        public_base_url='http://testserver/ml-check',teacher_logins=frozenset(),secure_cookie=False,testing=True)
    app=create_app(settings)
    with TestClient(app) as teacher, TestClient(app) as student:
        teacher.get('/ml-check/test-login?login=synthetic-teacher&role=teacher')
        student.get('/ml-check/test-login?login=synthetic-student&role=student')
        for bank in CURRENT_BANKS:
            gc.collect()  # Python3.14测试机及时释放上一课SQLite连接。
            page=teacher.get('/ml-check/teacher')
            r=teacher.post('/ml-check/teacher/session',data={'csrf_token':csrf(page.text),'lesson_id':bank.lesson_id},follow_redirects=False)
            assert r.status_code==303,(bank.lesson_id,'create',r.status_code)
            session=db.current_session(database)
            assert session['bank_version']==BANK_VERSION
            assert bank_from_snapshot(session['bank_json']).questions==bank.questions
            public=student.get('/ml-check/api/lessons/'+bank.lesson_id).json()
            assert all(set(q)=={'id','phase','prompt','options'} for q in public['questions'])
            def phase(value):
                page=teacher.get('/ml-check/teacher')
                assert teacher.post('/ml-check/teacher/phase',data={'csrf_token':csrf(page.text),'session_id':session['id'],'phase':value},follow_redirects=False).status_code==303
            for step in ['a','b']:
                phase(step)
                for index,q in enumerate(bank._by_phase(step)):
                    page=student.get('/ml-check/current')
                    text=html.unescape(page.text)
                    assert q['prompt'] in text,(bank.lesson_id,q['id'])
                    assert q['explanation'] not in text
                    answer=(q['answer']+1)%4 if step=='b' and index==0 else q['answer']
                    r=student.post('/ml-check/answer',data={'csrf_token':csrf(page.text),'session_id':session['id'],
                        'concept_id':q['concept_id'],'phase':step,'option_id':str(answer),'confidence':'sure'},follow_redirects=False)
                    assert r.status_code==303
                if step=='a':
                    phase('learn')
                    page=student.get('/ml-check/current'); text=html.unescape(page.text)
                    assert all(q['prompt'] not in text and q['explanation'] not in text for q in bank.questions)
                    assert all(item['title'] in text for item in bank.items)
                    assert student.post('/ml-check/learn/complete',data={'csrf_token':csrf(page.text),'session_id':session['id']},follow_redirects=False).status_code==303
            phase('result')
            text=html.unescape(student.get('/ml-check/current').text)
            assert all(q['explanation'] in text for q in bank.questions)
            row=dict(db.export_rows(database,session['id'])[0])
            assert tuple(row[k] for k in ['a_count','a_correct','learned','b_count','b_correct'])==(5,5,1,5,4)
            records.append({'lesson':bank.lesson_id,'A':'5/5','learning':True,'B':'4/5','feedback':True})
            print(bank.lesson_id,'full flow passed',flush=True)
result={'host':'hblu-5090','passed':len(records)==32,'bank_version':BANK_VERSION,'synthetic_flows':records,'production_sessions_created':0}
(HERE/'runtime-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
