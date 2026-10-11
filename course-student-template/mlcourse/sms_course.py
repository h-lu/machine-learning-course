"""NumPy teaching tools for lessons 10–14; offline and development-only by default."""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, re, time
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/sms'
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save_json(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def load_rows(split):
    if split not in ('train','dev'): raise ValueError('Only development partitions here; final evaluation uses the teacher entry after system selection.')
    path=DATA/f'{split}.csv'; meta=json.loads((DATA/'provenance.json').read_text())
    expected=meta['file_sha256'][f'course-student-template/data/sms/{split}.csv']
    if digest(path)!=expected: raise ValueError('Data bytes differ from fixed split')
    with path.open(encoding='utf-8',newline='') as f: return list(csv.DictReader(f))
def tokens(text):
    if not isinstance(text,str): raise ValueError('Text must be a string (empty text is permitted)')
    return re.findall(r"[a-z]+(?:'[a-z]+)?|\d+",text.lower())
def manual(texts):
    # Raw, interpretable counts; train-only scale below. No translation.
    return np.array([[len(t),sum(c.isdigit() for c in t),t.count('!'),len(tokens(t)),int('free' in tokens(t)),int(bool(re.search(r'https?://|www\.',t.lower())))] for t in texts],dtype=float)
def fit_representation(texts,kind='manual',max_features=1200):
    if kind=='manual':
        x=manual(texts); std=x.std(0);std[std<1e-12]=1
        return dict(kind=kind,mean=x.mean(0).tolist(),scale=std.tolist(),names=['characters','digits','exclamations','tokens','has_free','has_url'])
    if kind not in ('bow','tfidf'): raise ValueError('Unknown trainable representation')
    if not isinstance(max_features,int) or max_features<1: raise ValueError('max_features must be positive integer')
    df=Counter(t for text in texts for t in set(tokens(text)))
    vocab=sorted(df,key=lambda t:(-df[t],t))[:max_features]
    if not vocab: raise ValueError('Empty training vocabulary')
    return dict(kind=kind,names=vocab,idf=[float(np.log((1+len(texts))/(1+df[t]))+1) for t in vocab],normalization='L2 per row; empty row stays zero')
def transform(texts,rep):
    if rep['kind']=='manual': return (manual(texts)-rep['mean'])/rep['scale']
    names={v:i for i,v in enumerate(rep['names'])};x=np.zeros((len(texts),len(names)))
    for i,text in enumerate(texts):
        for token,n in Counter(tokens(text)).items():
            if token in names: x[i,names[token]]=n
    if rep['kind']=='tfidf': x*=np.array(rep['idf'])
    norms=np.linalg.norm(x,axis=1,keepdims=True);x/=np.maximum(norms,1e-12)
    return x

def sigmoid(z): return np.exp(-np.logaddexp(0,-np.asarray(z,dtype=float)))
def loss_gradient(x,y,w,b,l2=0.,sample_weights=None):
    a=np.ones(len(y)) if sample_weights is None else np.asarray(sample_weights,dtype=float)
    if len(y)==0 or not np.isfinite(x).all() or not np.isfinite(y).all() or not np.isin(y,[0,1]).all(): raise ValueError('Need finite nonempty binary data')
    if a.shape!=y.shape or not np.isfinite(a).all() or (a<=0).any() or not np.isfinite(l2) or l2<0: raise ValueError('Invalid weights or regularization')
    z=x@w+b;p=sigmoid(z);err=a*(p-y)/a.sum()
    loss=float(np.dot(a,np.logaddexp(0,z)-y*z)/a.sum()+l2*np.dot(w,w)/2)
    return loss,x.T@err+l2*w,float(err.sum())
def fit(x,y,dev_x,dev_y,lr=.2,steps=100,l2=.001,spam_weight=1.,seed=0,initial_scale=0.):
    if not isinstance(steps,int) or steps<1 or not np.isfinite(lr) or lr<=0 or not np.isfinite(spam_weight) or spam_weight<=0 or not np.isfinite(initial_scale) or initial_scale<0: raise ValueError('Invalid training setting')
    rng=np.random.default_rng(seed); w=rng.normal(0,initial_scale,x.shape[1]);b=0.;a=np.where(y==1,spam_weight,1.)
    trace=[];update=None
    for step in range(steps+1):
        loss,gw,gb=loss_gradient(x,y,w,b,l2,a)
        dev_loss,_,_=loss_gradient(dev_x,dev_y,w,b,0.)
        if not np.isfinite(loss) or not np.isfinite(gw).all(): raise ValueError('Training nonfinite; lower learning rate or inspect scale')
        trace.append(dict(step=step,train_objective=loss,dev_bce=dev_loss,intercept=b,weight_norm=float(np.linalg.norm(w)),gradient_norm=float(np.linalg.norm(gw)),train_bce=loss_gradient(x,y,w,b,0.)[0],tracked_dev_probability=float(sigmoid(dev_x[0]@w+b))))
        if step==steps:break
        if step==0:
            nw=w-lr*gw;nb=b-lr*gb
            update=dict(step=0,weights_before=w.tolist(),bias_before=b,gradient_weights=gw.tolist(),gradient_bias=gb,learning_rate=lr,weights_after=nw.tolist(),bias_after=nb,objective_before=loss,objective_after=loss_gradient(x,y,nw,nb,l2,a)[0],sample_x=x[0].tolist(),sample_y=float(y[0]),sample_p_before=float(sigmoid(x[0]@w+b)),sample_p_after=float(sigmoid(x[0]@nw+nb)),denominator=float(a.sum()),l2=l2,spam_weight=spam_weight,note='Full-batch gradient; first row illustrates prediction, does not alone determine update. Bias not penalized.')
        w-=lr*gw;b-=lr*gb
    return w,b,trace,update

def actions(p,ids,threshold=.5,capacity_fraction=1.):
    p=np.asarray(p)
    if len(ids)!=len(p) or len(set(ids))!=len(ids) or not np.isfinite(p).all() or ((p<0)|(p>1)).any():raise ValueError('Invalid probabilities/IDs')
    if not 0<=threshold<=1 or not 0<=capacity_fraction<=1:raise ValueError('Threshold/capacity must be in [0,1]')
    order=sorted((i for i in range(len(p)) if p[i]>=threshold),key=lambda i:(-p[i],ids[i]))
    out=np.zeros(len(p),dtype=int);out[order[:int(np.floor(len(p)*capacity_fraction))]]=1
    return out

def metrics(y,p,action):
    y=np.asarray(y);tp=int(((action==1)&(y==1)).sum());fp=int(((action==1)&(y==0)).sum());fn=int(((action==0)&(y==1)).sum());tn=int(((action==0)&(y==0)).sum())
    return dict(n=len(y),tp=tp,fp=fp,fn=fn,tn=tn,reviewed=int(action.sum()),precision=None if tp+fp==0 else tp/(tp+fp),recall=None if tp+fn==0 else tp/(tp+fn),accuracy=(tp+tn)/len(y),brier=float(np.mean((p-y)**2)))
def write_csv(path,rows):
    with Path(path).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def read_cache(rows,split):
    from mlcourse.sms_encoder import load_cache
    return load_cache(rows, DATA/'cache'/split)
def run(config,output):
    allowed={'representation','max_features','lr','steps','l2','spam_weight','seed','initial_scale','threshold','capacity_fraction'}
    if set(config)-allowed: raise ValueError('Unknown settings: '+str(sorted(set(config)-allowed)))
    start=time.perf_counter();out=Path(output)
    if out.exists() and any(out.iterdir()): raise ValueError('Use a new output directory to preserve comparisons')
    out.mkdir(parents=True,exist_ok=True)
    train,dev=load_rows('train'),load_rows('dev');kind=config.get('representation','manual')
    if kind=='pretrained':
        rep={'kind':kind,'encoder_manifest_sha256':digest(DATA/'encoder/manifest.json'),'dimension':384,'names':[f'encoder_{i}' for i in range(384)]}
        x,dx=read_cache(train,'train'),read_cache(dev,'dev')
    else:
        rep=fit_representation([r['text'] for r in train],kind,config.get('max_features',1200));x=transform([r['text'] for r in train],rep);dx=transform([r['text'] for r in dev],rep)
    y=np.array([r['label']=='spam' for r in train],dtype=float);dy=np.array([r['label']=='spam' for r in dev],dtype=float)
    effective=dict(representation=kind,max_features=config.get('max_features',1200),lr=config.get('lr',1.),steps=config.get('steps',400),l2=config.get('l2',.001),spam_weight=config.get('spam_weight',1.),seed=config.get('seed',0),initial_scale=config.get('initial_scale',0.),threshold=config.get('threshold',.5),capacity_fraction=config.get('capacity_fraction',1.))
    w,b,trace,update=fit(x,y,dx,dy,**{k:effective[k] for k in ('lr','steps','l2','spam_weight','seed','initial_scale')})
    p=sigmoid(dx@w+b);action=actions(p,[r['id'] for r in dev],effective['threshold'],effective['capacity_fraction'])
    records=[dict(id=r['id'],group_id=r['group_id'],label=r['label'],probability=float(prob),action=int(act),text_sha256=r['text_sha256']) for r,prob,act in zip(dev,p,action)]
    save_json(out/'representation.json',rep);save_json(out/'config.json',effective);save_json(out/'first_update.json',dict(update,sample_id=train[0]['id']))
    np.savez(out/'model.npz',w=w,b=np.array(b));write_csv(out/'curve.csv',trace);write_csv(out/'records.csv',records)
    save_json(out/'prediction_trace.json',dict(id=dev[0]['id'],x=dx[0].tolist(),weights=w.tolist(),contributions=(dx[0]*w).tolist(),intercept=b,logit=float(dx[0]@w+b),probability=float(p[0]),action=int(action[0]),feature_names=rep['names'],text_sha256=dev[0]['text_sha256']))
    summary=dict(metrics=metrics(dy,p,action),partition='dev',training_rows=len(train),dimensions=x.shape[1],final_test_opened=False,config=effective,data_manifest_sha256=digest(DATA/'split_manifest.csv'),code_sha256=digest(__file__))
    save_json(out/'summary.json',summary);return dict(summary,seconds=time.perf_counter()-start)
