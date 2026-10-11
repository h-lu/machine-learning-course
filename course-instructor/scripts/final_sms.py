"""Lesson 14 only, after selection. Offline public-data protocol, not an access barrier."""
from pathlib import Path
import argparse,csv,json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'course-student-template'))
from mlcourse.sms_course import digest,save_json,DATA,transform,sigmoid,actions,metrics,write_csv
from mlcourse.sms_encoder import load_cache

def evaluate(system,vault=None):
    system=Path(system);receipt=system/'final_result.json'
    if receipt.exists():raise ValueError('This system already has its first final evaluation; preserve it')
    lock=json.loads((system/'system_lock.json').read_text());vault=Path(vault) if vault else ROOT/'course-instructor/resources/sms'
    for name,sha in lock['files'].items():
        if digest(system/name)!=sha:raise ValueError('Selected system changed: '+name)
    if lock['data_manifest_sha256']!=digest(DATA/'split_manifest.csv') or lock['code_sha256']!=digest(ROOT/'course-student-template/mlcourse/sms_course.py'):raise ValueError('Selected data/code changed')
    provenance=json.loads((DATA/'provenance.json').read_text());path=vault/'finalholdout.csv'
    if digest(path)!=provenance['file_sha256']['course-instructor/resources/sms/finalholdout.csv']:raise ValueError('Final data identity changed')
    with path.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    cfg=json.loads((system/'config.json').read_text());rep=json.loads((system/'representation.json').read_text())
    if rep['kind']=='pretrained':
        if rep['encoder_manifest_sha256']!=digest(DATA/'encoder/manifest.json'):raise ValueError('Encoder version changed')
        x=load_cache(rows,vault/'cache/finalholdout')
    else:x=transform([r['text'] for r in rows],rep)
    model=np.load(system/'model.npz',allow_pickle=False);p=sigmoid(x@model['w']+model['b']);y=np.array([r['label']=='spam' for r in rows],dtype=float);a=actions(p,[r['id'] for r in rows],cfg['threshold'],cfg['capacity_fraction'])
    write_csv(system/'final_records.csv',[dict(id=r['id'],label=r['label'],probability=float(v),action=int(t)) for r,v,t in zip(rows,p,a)])
    result=dict(metrics=metrics(y,p,a),system_lock_sha256=digest(system/'system_lock.json'),partition='finalholdout',policy='Do not tune from these results; subsequent modifications require new independent evaluation.')
    save_json(receipt,result);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--system',required=True);a=p.parse_args();print(json.dumps(evaluate(a.system),indent=2))
