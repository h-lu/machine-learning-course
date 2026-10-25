"""Frozen encoder plus trainable head, retaining lessons 10–12 unchanged."""
from pathlib import Path
import json,time
import numpy as np
from mlcourse import sms_course as base
from mlcourse import text_representations as lexical
from mlcourse.sms_encoder import Encoder,load_cache

def run(cfg,output):
 if cfg.get('representation')!='pretrained':return lexical.run(cfg,output)
 defaults=dict(representation='pretrained',lr=1.,steps=400,l2=.001,spam_weight=1.,seed=0,initial_scale=0.,threshold=.5,capacity_fraction=1.,trace_id=None)
 if set(cfg)-set(defaults):raise ValueError('Unknown pretrained setting')
 c={**defaults,**cfg};out=Path(output)
 if out.exists():raise ValueError('Use a new output directory')
 train,dev=base.load_rows('train'),base.load_rows('dev')
 x=load_cache(train,base.DATA/'cache/train');dx=load_cache(dev,base.DATA/'cache/dev')
 y=np.array([r['label']=='spam' for r in train],float);dy=np.array([r['label']=='spam' for r in dev],float)
 w,b,curve,update=base.fit(x,y,dx,dy,**{k:c[k] for k in ['lr','steps','l2','spam_weight','seed','initial_scale']})
 p=base.sigmoid(dx@w+b);a=base.actions(p,[r['id'] for r in dev],c['threshold'],c['capacity_fraction'])
 i=0 if c['trace_id'] is None else next((i for i,r in enumerate(dev) if r['id']==c['trace_id']),None)
 if i is None:raise ValueError('Unknown dev ID')
 rep=dict(kind='pretrained',dimension=384,encoder_manifest_sha256=base.digest(base.DATA/'encoder/manifest.json'))
 trace=dict(id=dev[i]['id'],text=dev[i]['text'],text_sha256=dev[i]['text_sha256'],x=dx[i].tolist(),weights=w.tolist(),contributions=(dx[i]*w).tolist(),intercept=b,logit=float(dx[i]@w+b),probability=float(p[i]),action=int(a[i]),top_absolute_contribution_indices=np.argsort(np.abs(dx[i]*w))[-8:][::-1].tolist())
 summary=dict(metrics=base.metrics(dy,p,a),partition='dev',final_test_opened=False,training_rows=len(train),dimensions=384,encoder_frozen=True,config=c,data_manifest_sha256=base.digest(base.DATA/'split_manifest.csv'),code_sha256=base.digest(__file__))
 out.mkdir(parents=True)
 for name,v in [('representation',rep),('config',c),('summary',summary),('prediction_trace',trace),('first_update',update)]:base.save_json(out/(name+'.json'),v)
 np.savez(out/'model.npz',w=w,b=np.array(b));base.write_csv(out/'curve.csv',curve)
 base.write_csv(out/'records.csv',[dict(id=r['id'],group_id=r['group_id'],label=r['label'],probability=float(v),action=int(t),text_sha256=r['text_sha256']) for r,v,t in zip(dev,p,a)])
 return summary

def predict_new(texts,system,output):
 """True CPU encoding of new English, not lookup of cached SMS."""
 system=Path(system);out=Path(output)
 if out.exists():raise ValueError('Preserve previous probe')
 rep=json.loads((system/'representation.json').read_text());cfg=json.loads((system/'config.json').read_text())
 if rep['kind']!='pretrained':raise ValueError('Use a pretrained classifier with the same encoder')
 if rep['encoder_manifest_sha256']!=base.digest(base.DATA/'encoder/manifest.json'):raise ValueError('Encoder changed')
 enc=Encoder();x=enc.encode(texts);m=np.load(system/'model.npz',allow_pickle=False);p=base.sigmoid(x@m['w']+m['b'])
 # Capacity is batch-dependent; isolated probes intentionally report probabilities only.
 result=dict(texts=texts,vectors=x.tolist(),probabilities=p.tolist(),encoder_manifest_sha256=rep['encoder_manifest_sha256'],classifier_sha256=base.digest(system/'model.npz'),real_cpu_encoding=True,ground_truth_labels=None,note='Unlabelled probes test sensitivity, not accuracy; capacity actions require defined evaluation batch')
 base.save_json(out,result);return result
