"""Development-based selection receipt, not access control or automatic selection."""
from pathlib import Path
import argparse,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from mlcourse.sms_course import digest,save_json,DATA
FILES=['model.npz','representation.json','config.json','summary.json']
CODE=['mlcourse/sms_course.py','mlcourse/text_representations.py','mlcourse/transfer13.py','mlcourse/sms_encoder.py','lesson-14/lock_system.py']
def lock(run,out,reason):
 run,out=Path(run),Path(out)
 if not reason.strip():raise ValueError('Give development evidence for selection')
 if out.exists():raise ValueError('Preserve the existing selected system')
 s=json.loads((run/'summary.json').read_text());cfg=json.loads((run/'config.json').read_text());rep=json.loads((run/'representation.json').read_text())
 if s.get('partition')!='dev' or s.get('final_test_opened') is not False:raise ValueError('Select from development only')
 expected=ROOT/('mlcourse/transfer13.py' if rep['kind']=='pretrained' else 'mlcourse/text_representations.py')
 if s['code_sha256']!=digest(expected) or s['data_manifest_sha256']!=digest(DATA/'split_manifest.csv'):raise ValueError('Stale code or data; redo development')
 if s['config']!=cfg or cfg['representation']!=rep['kind']:raise ValueError('Inconsistent run settings')
 out.mkdir(parents=True)
 for f in FILES:shutil.copyfile(run/f,out/f)
 receipt=dict(reason=reason,files={f:digest(out/f) for f in FILES},code_files={f:digest(ROOT/f) for f in CODE},data_manifest_sha256=digest(DATA/'split_manifest.csv'),policy='Only the first evaluation of a selected system is final. A new folder cannot make already-seen labels independent again.')
 save_json(out/'system_lock.json',receipt);return receipt
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output',required=True);p.add_argument('--reason',required=True);a=p.parse_args();print(json.dumps(lock(a.run,a.output,a.reason),ensure_ascii=False,indent=2))
