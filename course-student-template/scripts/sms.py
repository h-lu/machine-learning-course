"""Thin optional experiment/encoding tools. Not a complete student report."""
from pathlib import Path
import argparse,json,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mlcourse.sms_course import run,save_json
p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
r=sub.add_parser('run');r.add_argument('--config',required=True,type=Path);r.add_argument('--output',required=True,type=Path)
e=sub.add_parser('encode');e.add_argument('--text',required=True,action='append');e.add_argument('--output',required=True,type=Path)
a=p.parse_args()
if a.command=='run': print(json.dumps(run(json.loads(a.config.read_text()),a.output),ensure_ascii=False,indent=2))
else:
    from mlcourse.sms_encoder import Encoder
    if a.output.exists():raise ValueError('Use a new output path')
    start=time.perf_counter();encoder=Encoder();loaded=time.perf_counter();x=encoder.encode(a.text)
    save_json(a.output,dict(texts=a.text,vectors=x.tolist(),model=encoder.manifest,updated_parameters=[]))
    print(f'encoded {len(x)} texts; dimension 384; CPU; frozen; load {loaded-start:.4f}s; encode {time.perf_counter()-loaded:.4f}s')
