"""Starter: training mean only. Choose/build the comparison in your own analysis."""
from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mlcourse.bike_starter import load_development
from mlcourse.sms_course import save_json,write_csv
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=Path(__file__).with_name('config.json'));p.add_argument('--compare',action='store_true',help='Optional worked code: read/change choices; not a finished investigation');p.add_argument('--output',type=Path,default=Path(__file__).parent/'artifacts/baseline');a=p.parse_args()
if a.output.exists() and any(a.output.iterdir()):raise ValueError('Use new output directory')
a.output.mkdir(parents=True,exist_ok=True);train,dev,audit=load_development(Path(__file__).resolve().parents[1])
if a.compare:
    from mlcourse.bike_models09 import compare
    cfg=json.loads(a.config.read_text());pred,trace,score=compare(train,dev,fields=cfg['fields'],depth=cfg['depth']);save_json(a.output/'trace.json',trace)
else:
    pred={'training_mean':np.full(len(dev),np.mean([r['cnt'] for r in train]))};score={k:float(np.mean([abs(vv-r['cnt']) for vv,r in zip(v,dev)])) for k,v in pred.items()}
write_csv(a.output/'records.csv',[dict(instant=r['instant'],method=k,actual=r['cnt'],prediction=float(v),absolute_error=abs(float(v)-r['cnt'])) for k,values in pred.items() for r,v in zip(dev,values)])
save_json(a.output/'summary.json',dict(partition='validation',mae=score,train_rows=len(train),dev_rows=len(dev),old_test='historical only; not opened here'));print(score)
