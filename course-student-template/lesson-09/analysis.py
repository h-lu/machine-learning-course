"""第9课运行入口：默认计算训练均值基线；加 --compare 比较线性模型与浅树。"""
from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mlcourse.bike_starter import load_development
from mlcourse.sms_course import save_json,write_csv
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=Path(__file__).with_name('config.json'));p.add_argument('--trace-id',type=int,help='追踪指定验证记录的instant编号；须同时使用 --compare');p.add_argument('--compare',action='store_true',help='运行线性模型与浅树的比较；分组检查、解释和建议仍由你完成');p.add_argument('--output',type=Path,default=Path(__file__).parent/'artifacts/baseline');a=p.parse_args()
if a.trace_id is not None and not a.compare:p.error('指定 --trace-id 时，需要同时加上 --compare，才能追踪两种模型的预测')
if a.output.exists() and any(a.output.iterdir()):raise ValueError('结果目录里已有文件。请用 --output 换一个新目录名，保留原来的结果')
a.output.mkdir(parents=True,exist_ok=True);train,dev,audit=load_development(Path(__file__).resolve().parents[1])
if a.compare:
    from mlcourse.bike_models09 import compare
    cfg=json.loads(a.config.read_text());matches=[i for i,r in enumerate(dev) if r['instant']==a.trace_id] if a.trace_id is not None else [0]
    if not matches:p.error('这个编号不属于本课验证集。请从本次 records.csv 中选择一个 instant 编号')
    pred,trace,score=compare(train,dev,fields=cfg['fields'],depth=cfg['depth'],trace_index=matches[0]);save_json(a.output/'trace.json',trace)
else:
    pred={'training_mean':np.full(len(dev),np.mean([r['cnt'] for r in train]))};score={k:float(np.mean([abs(vv-r['cnt']) for vv,r in zip(v,dev)])) for k,v in pred.items()}
write_csv(a.output/'records.csv',[dict(instant=r['instant'],method=k,actual=r['cnt'],prediction=float(v),absolute_error=abs(float(v)-r['cnt'])) for k,values in pred.items() for r,v in zip(dev,values)])
save_json(a.output/'summary.json',dict(partition='validation',mae=score,train_rows=len(train),dev_rows=len(dev),old_test='historical only; not opened here',config=cfg if a.compare else {'method':'training_mean'}));print(score)
