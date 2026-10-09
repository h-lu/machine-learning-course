"""重放第08课个人研究证据；默认仅主验证，--with-test才显式评价已选方法。"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

REPO=Path(__file__).resolve().parents[2]
INPUTS=Path(__file__).with_name('cold_read_08_student')
EXPECTED=Path(__file__).with_name('cold_read_08_20261009.json')


def run(root, arguments, forbid_test=False):
    env=dict(os.environ)
    if forbid_test:
        env['ML08_FORBID_TEST']='1'
    result=subprocess.run([sys.executable,*arguments],cwd=root,env=env,text=True,capture_output=True,timeout=60)
    if result.returncode:
        message=(result.stderr+result.stdout)[-1500:].replace(str(root),'student-copy')
        raise RuntimeError(message)
    return result.returncode


def close(actual, expected):
    assert math.isclose(actual,expected,abs_tol=1e-9), (actual,expected)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-test',action='store_true',help='选择被冻结后显式重算该方法的官方最后测试')
    args=parser.parse_args()
    expected=json.loads(EXPECTED.read_text())
    for name,digest in expected['preserved_inputs']['sha256'].items():
        assert hashlib.sha256((INPUTS/name).read_bytes()).hexdigest()==digest,name
    with tempfile.TemporaryDirectory(prefix='ml08-replay-') as directory:
        root=Path(directory)/'student'
        shutil.copytree(REPO/'course-student-template',root,
                        ignore=shutil.ignore_patterns('.git','__pycache__','artifacts'))
        # 先确认薄起点和热身可运行；研究输入只来自已保存的个人设计。
        run(root,['lesson-08/analysis.py'])
        run(root,['scripts/lesson08.py','warmup','--output','lesson-08/artifacts/warmup'])
        for name in ['plan.md','personal-config.json','research.py','contract.json']:
            shutil.copyfile(INPUTS/name,root/'lesson-08'/name)
        plan_before=hashlib.sha256((root/'lesson-08/plan.md').read_bytes()).hexdigest()
        run(root,['lesson-08/research.py','--output','lesson-08/artifacts/first-personal-validation'])
        validation=json.loads((root/'lesson-08/artifacts/first-personal-validation/summary.json').read_text())
        assert validation['plan_sha256']==plan_before
        for actual,wanted in zip(validation['metrics'],expected['validation'],strict=True):
            assert actual['method']==wanted['method'] and actual['n']==wanted['n']
            close(actual['overall_mae'],wanted['overall_mae'])
            close(actual['night_mae'],wanted['night_mae'])
        # 在自己的逐条输出之外，用原CSV训练计数重新核算规则与五条失败。
        with (root/'data/bike/hour.csv').open() as stream:
            raw=list(csv.DictReader(stream))
        train=[r for r in raw if r['dteday']<'2012-07-01' and int(r['hr'])<6]
        mean=sum(int(r['cnt']) for r in train)/len(train)
        close(mean,expected['independent_calculation']['night_prediction'])
        valid=[r for r in raw if '2012-07-01'<=r['dteday']<'2012-10-01' and int(r['hr'])<6]
        close(sum(abs(mean-int(r['cnt'])) for r in valid[:5])/5,
              expected['independent_calculation']['five_mae'])
        close(sum(abs(mean-int(r['cnt'])) for r in valid)/len(valid),
              expected['independent_calculation']['full_night_mae'])
        # 验证证据哈希匹配后才放入已保存选择；不按本次测试重新选择。
        decision=json.loads((INPUTS/'decision.json').read_text())
        comparison=root/'lesson-08/artifacts/first-personal-validation/comparison.csv'
        assert hashlib.sha256(comparison.read_bytes()).hexdigest()==decision['validation_sha256']
        for name in ['decision.json','report.md','submission.json','independent-check.json','upgrade.json']:
            shutil.copyfile(INPUTS/name,root/'lesson-08'/name)
        choice_before=hashlib.sha256((root/'lesson-08/decision.json').read_bytes()).hexdigest()
        test_result=None
        if args.with_test:
            run(root,['lesson-08/research.py','--split','test','--decision','lesson-08/decision.json',
                      '--selected-method',decision['selected_method'],'--output','lesson-08/artifacts/selected-test'])
            test=json.loads((root/'lesson-08/artifacts/selected-test/summary.json').read_text())
            assert test['methods']==[decision['selected_method']]
            test_result=test['metrics']
            for actual,wanted in zip(test_result,expected['selected_test'],strict=True):
                assert actual['n']==wanted['n']
                close(actual['overall_mae'],wanted['overall_mae'])
                close(actual['night_mae'],wanted['night_mae'])
        run(root,['scripts/course.py','run','08'],forbid_test=True)
        run(root,['scripts/course.py','check','08'],forbid_test=True)
        run(root,['scripts/course.py','ci'],forbid_test=True)
        assert hashlib.sha256((root/'lesson-08/decision.json').read_bytes()).hexdigest()==choice_before
        print(json.dumps({'lesson':'08/S06','validation':validation['metrics'],
                          'selected_test':test_result,'run_check_ci':'passed',
                          'test_automatic_in_ci':False,'independent_five':'passed',
                          'kind':'软件重放；非真人试教'},ensure_ascii=False))

if __name__=='__main__':
    main()
