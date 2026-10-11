"""Author simulating AI-assisted student analysis; not a course-provided solution.
Choices are in my-plan.json: commute focus, shallow depth 3 vs original depth 2.
"""
from pathlib import Path
import json,sys,csv
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from mlcourse.bike_starter import load_development
from mlcourse.bike_models09 import compare,tree_predict
from mlcourse.sms_course import save_json,write_csv
OUT=Path(__file__).parent/'artifacts/my-study'
if OUT.exists() and any(OUT.iterdir()):raise ValueError('Keep old evidence; choose a fresh directory or use the reproduction checker')
OUT.mkdir(parents=True,exist_ok=True)
train,dev,audit=load_development(ROOT);plan=json.loads(Path(__file__).with_name('my-plan.json').read_text());cfg=json.loads(Path(__file__).with_name('my-depth3.json').read_text())
pred2,trace2,_=compare(train,dev,fields=cfg['fields'],depth=2);pred3,trace3,_=compare(train,dev,fields=cfg['fields'],depth=cfg['depth'])
pred={'linear':pred2['linear'],'tree_depth2':pred2['shallow_tree'],'tree_depth3':pred3['shallow_tree']};actual=np.array([r['cnt'] for r in dev],dtype=float)
commute=np.array([r['workingday']==1 and r['hr'] in (8,17,18) for r in dev]);groups={'all':np.ones(len(dev),dtype=bool),'commute':commute,'other':~commute}
metrics=[]
for name,p in pred.items():
 for group,mask in groups.items():
  err=p[mask]-actual[mask];metrics.append(dict(method=name,group=group,n=int(mask.sum()),mae=float(np.abs(err).mean()),mean_signed_error=float(err.mean())))
write_csv(OUT/'comparison.csv',metrics)
write_csv(OUT/'records.csv',[dict(instant=r['instant'],date=r['dteday'],hr=r['hr'],workingday=r['workingday'],group='commute' if commute[i] else 'other',method=name,actual=r['cnt'],prediction=float(p[i]),absolute_error=abs(float(p[i])-r['cnt'])) for name,p in pred.items() for i,r in enumerate(dev)])
# Diagnostic record selected within the predeclared group AFTER observing errors.
# It is explicitly a failure illustration, not a representative random sample.
idx=max(np.flatnonzero(commute),key=lambda i:abs(pred['tree_depth3'][i]-actual[i]));r=dev[idx];raw=np.array([r[f] for f in cfg['fields']]);std=(raw-trace3['train_mean'])/trace3['train_scale'];vector=np.r_[1.,std];coeff=np.array(trace3['coefficients']);contributions=vector*coeff;tree_value,path=tree_predict(trace3['tree_model'],raw)
# Independently collect training rows following that leaf's conditions.
leaf=train
for step in path[:-1]:
 field=cfg['fields'][step['feature']];cut=step['threshold'];branch=step['branch'];leaf=[r for r in leaf if (r[field]<=cut)==(branch=='left')]
leaf_mean=sum(r['cnt'] for r in leaf)/len(leaf)
assert abs(leaf_mean-tree_value)<1e-10
assert abs(float(sum(contributions))-pred['linear'][idx])<1e-9
save_json(OUT/'chosen-record.json',dict(instant=r['instant'],date=r['dteday'],hr=r['hr'],actual=r['cnt'],selection='largest absolute tree_depth3 error among the predeclared commute group, chosen for diagnosis not representativeness',fields=['intercept_constant']+cfg['fields'],raw=raw.tolist(),standardized_with_constant=vector.tolist(),train_mean=trace3['train_mean'],train_scale=trace3['train_scale'],coefficients=coeff.tolist(),contributions=contributions.tolist(),linear=float(sum(contributions)),tree_depth2=float(pred['tree_depth2'][idx]),tree_depth3=tree_value,tree_path=path,leaf_count_independent=len(leaf),leaf_mean_independent=leaf_mean))
# Transfer exercise, changed conflict observation; do not borrow teacher answers.
toyx=np.array([0.,1.,1.,2.]);toyy=np.array([1.,2.,6.,5.]);w=sum((toyx-toyx.mean())*(toyy-toyy.mean()))/sum((toyx-toyx.mean())**2);b=toyy.mean()-w*toyx.mean()
save_json(OUT/'transfer.json',dict(changed_sample=[1,6],slope=float(w),intercept=float(b),old_parameters_unchanged=False,warning='Changing a target can alter the fitted intercept even when the slope happens to stay unchanged.'))
save_json(OUT/'summary.json',dict(plan=plan,config=cfg,train_n=len(train),dev_n=len(dev),commute_n=int(commute.sum()),test_opened=False,models=list(pred),data_sha256=audit.get('sha256','see official source'),purpose='same-hour conditional estimation, not future dispatch or causal intervention'))
print(json.dumps(metrics,indent=2));print('diagnostic ID',r['instant'])
