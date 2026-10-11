"""Teacher preflight; label-blind frozen encoding, partitions saved separately."""
from pathlib import Path
import csv,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'course-student-template'))
from mlcourse.sms_course import load_rows,DATA,save_json
from mlcourse.sms_encoder import Encoder,cache
if __name__=='__main__':
    encoder=Encoder(); evidence=[]
    for split in ('train','dev'):
        evidence.append(cache(load_rows(split),DATA/'cache'/split,encoder))
    vault=ROOT/'course-instructor/resources/sms'
    with (vault/'finalholdout.csv').open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
    evidence.append(cache(rows,vault/'cache/finalholdout',encoder))
    save_json(ROOT/'validation/lessons09-14/encoding.json',[{k:v for k,v in m.items() if k not in ('ids','text_sha256')} for m in evidence])
    print([(m['split'],len(m['ids']),m['seconds']) for m in evidence])
