"""Save the chosen system BEFORE final evaluation; hashes bind exact fitted objects."""
from pathlib import Path
import argparse,json,shutil,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mlcourse.sms_course import digest,save_json,DATA
FILES=['model.npz','representation.json','config.json','summary.json']
def lock(run,out,reason):
    run,out=Path(run),Path(out)
    if not reason.strip():raise ValueError('Explain the development-based selection')
    if out.exists():raise ValueError('A selection already exists; use a new version before any final evaluation')
    summary=json.loads((run/'summary.json').read_text())
    if summary['code_sha256']!=digest(Path(__file__).resolve().parents[1]/'mlcourse/sms_course.py') or summary['data_manifest_sha256']!=digest(DATA/'split_manifest.csv'):raise ValueError('Run predates current code/data; rerun development before selecting')
    if summary['partition']!='dev' or summary['final_test_opened']:raise ValueError('Selection must use development evidence')
    out.mkdir(parents=True)
    for f in FILES:shutil.copyfile(run/f,out/f)
    record=dict(reason=reason,files={f:digest(out/f) for f in FILES},data_manifest_sha256=digest(DATA/'split_manifest.csv'),code_sha256=digest(Path(__file__).resolve().parents[1]/'mlcourse/sms_course.py'),test_policy='First final evaluation only after this selection. If results inform changes, obtain new independent data.')
    save_json(out/'system_lock.json',record);return record
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--output',required=True);p.add_argument('--reason',required=True);a=p.parse_args();lock(a.run,a.output,a.reason)
