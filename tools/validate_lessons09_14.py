"""Local author validation, no GitHub Actions, no network, no student submissions.
Independent scalar recomputation and boundary checks; not a human classroom trial.
"""
from pathlib import Path
from collections import defaultdict
import argparse,csv,hashlib,importlib.util,json,os,platform,re,subprocess,sys,tempfile,time,resource
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import numpy as np
ROOT=Path(__file__).resolve().parents[1];STUDENT=ROOT/'course-student-template';sys.path.insert(0,str(STUDENT))
from mlcourse import sms_course as m
from mlcourse.sms_encoder import Encoder,load_cache

def read(path):return json.loads(Path(path).read_text())
def rows(path):
    with Path(path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
def require(x,msg):
    if not x:raise AssertionError(msg)
def rejects(fn,msg):
    try:fn()
    except (ValueError,FileNotFoundError):return
    raise AssertionError(msg)
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v

def boundaries():
    x=np.array([[0.],[1.]]);y=np.array([0.,1.]);w=np.array([0.]);b=0.
    loss,gw,gb=m.loss_gradient(x,y,w,b,.1)
    require(abs(loss-np.log(2))<1e-12 and abs(gw[0]+.25)<1e-12 and abs(gb)<1e-12,'hand gradient')
    nw,nb,curve,update=m.fit(x,y,x,y,lr=1,steps=1,l2=.1)
    require(abs(nw[0]-.25)<1e-12 and abs(nb)<1e-12,'hand update')
    # Independent finite differences at nonzero weights, bias, uneven sample weights.
    x=np.array([[1.,2.],[-1.,.2],[0.,3.]]);y=np.array([1.,0.,1.]);w=np.array([.3,-.2]);b=.1;a=np.array([2.,1.,2.]);lam=.07
    def scalar(ww,bb):
        import math
        return sum(float(aa)*(math.log1p(math.exp(float(sum(xx*ww)+bb)))-float(yy)*(float(sum(xx*ww)+bb))) for xx,yy,aa in zip(x,y,a))/sum(a)+lam*sum(ww**2)/2
    _,g,gb=m.loss_gradient(x,y,w,b,lam,a);eps=1e-6
    for j in range(2):
        delta=np.eye(2)[j]*eps;require(abs(g[j]-(scalar(w+delta,b)-scalar(w-delta,b))/(2*eps))<1e-8,'finite difference weight')
    require(abs(gb-(scalar(w,b+eps)-scalar(w,b-eps))/(2*eps))<1e-8,'finite difference bias')
    for kind in ('manual','bow','tfidf'):
        rep=m.fit_representation(['green tea','tea tea','red coffee'],kind);before=json.dumps(rep,sort_keys=True);z=m.transform(['','zzzznewword','中文🙂'],rep);require(np.isfinite(z).all(),'empty/OOV finite');require(json.dumps(rep,sort_keys=True)==before,'dev transform must not fit')
        if kind!='manual':require(np.all(z==0),'OOV zero vector')
    for cfg in ({'lr':0},{'lr':float('nan')},{'steps':-1},{'spam_weight':0},{'l2':-1}):rejects(lambda:m.fit(x,y,x,y,**cfg),'invalid training settings accepted')
    rejects(lambda:m.actions(np.array([.5]),['a'],float('nan'),1),'NaN threshold')
    rejects(lambda:m.actions(np.array([.5]),['a'],.5,-1),'negative capacity')
    require(m.actions(np.array([.5,.5]),['b','a'],.5,.5).tolist()==[0,1],'deterministic capacity tie')
    require(m.actions(np.array([1.,0.]),['a','b'],0,0).sum()==0,'zero capacity')
    require(m.metrics(np.array([1.,0.]),np.array([.3,.2]),np.array([0,0]))['precision'] is None,'undefined precision')
    require(np.isfinite(m.sigmoid(np.array([-1000,0,1000]))).all(),'stable sigmoid')
    z1=m.fit(x,y,x,y,steps=3,seed=7,initial_scale=.1)[0];z2=m.fit(x,y,x,y,steps=3,seed=7,initial_scale=.1)[0];require(np.array_equal(z1,z2),'seed repeatability')
    rejects(lambda:m.load_rows('finalholdout'),'default loader leaks final')
    return dict(hand_objective_after=update['objective_after'],finite_difference_tolerance=1e-8,edge_cases='OOV, empty, Unicode, NaN, negative settings, zero capacity, tied IDs, extreme logits, seed repeatability; development transform immutable')

def data_audit():
    manifest=rows(m.DATA/'split_manifest.csv');groups=defaultdict(set)
    for r in manifest:groups[r['group_id']].add(r['split'])
    require(all(len(v)==1 for v in groups.values()),'group crosses partitions')
    allrows=m.load_rows('train')+m.load_rows('dev')+rows(ROOT/'course-instructor/resources/sms/finalholdout.csv')
    require(len(allrows)==len(manifest)==5574 and len({r['id'] for r in allrows})==5574,'record identity/count')
    source=module(ROOT/'tools/prepare_sms.py','prep_sms');known={r['id']:r for r in allrows};norm=defaultdict(set)
    for r in allrows:
        require(hashlib.sha256(r['text'].encode()).hexdigest()==r['text_sha256'],'raw text hash')
        norm[source.normal(r['text'])].add(r['split'])
    require(all(len(v)==1 for v in norm.values()),'exact normalized duplicate leakage')
    edges=rows(ROOT/'course-instructor/resources/sms/group_edges.csv')
    for e in edges:
        l,r=known[e['left']],known[e['right']];require(l['group_id']==r['group_id'],'edge not grouped')
        if e['rule']=='char3_jaccard':
            t,u=source.normal(l['text']),source.normal(r['text']);a={t[i:i+3] for i in range(len(t)-2)};b={u[i:i+3] for i in range(len(u)-2)};require(len(a&b)/len(a|b)>=.85,'invalid near duplicate edge')
    # Recompute label-blind grouping from reversed input; partition groups must be order invariant.
    reversed_rows=list(reversed(allrows));g,_=source.group_texts([r['text'] for r in reversed_rows]);observed=defaultdict(set)
    for r,label in zip(reversed_rows,g):observed[label].add(r['group_id'])
    require(all(len(v)==1 for v in observed.values()) and len(observed)==len(groups),'group ordering stability/closure')
    for split in ('train','dev'):
        rs=m.load_rows(split);load_cache(rs,m.DATA/'cache'/split)
        rejects(lambda:load_cache(list(reversed(rs)),m.DATA/'cache'/split),'cache accepted wrong ID order')
    return dict(rows=5574,groups=len(groups),edges_verified=len(edges),reversed_grouping_matches=True,leakage='no group spans train/dev/finalholdout; exact and defined near duplicates grouped before split')

def scalar_recompute(out):
    rs=rows(out/'records.csv');tp=fp=fn=tn=0
    for r in rs:
        positive=r['label']=='spam';act=int(r['action'])==1
        tp+=positive and act;fp+=(not positive) and act;fn+=positive and not act;tn+=(not positive) and not act
    stored=read(out/'summary.json')['metrics'];require([tp,fp,fn,tn]==[stored[k] for k in ('tp','fp','fn','tn')],'confusion matrix mismatch')
    trace=read(out/'prediction_trace.json');z=sum(a*b for a,b in zip(trace['x'],trace['weights']))+trace['intercept'];require(abs(z-trace['logit'])<1e-9,'prediction contributions mismatch')
    update=read(out/'first_update.json')
    for a,g,b in zip(update['weights_before'],update['gradient_weights'],update['weights_after']):require(abs(a-update['learning_rate']*g-b)<1e-12,'update mismatch')
    require(abs(update['bias_before']-update['learning_rate']*update['gradient_bias']-update['bias_after'])<1e-12,'bias update mismatch')
    return dict(tp=tp,fp=fp,fn=fn,tn=tn,trace_logit=z)

def run_checks(destination):
    evidence=dict(python=sys.version,platform=platform.platform(),threads=1,scope='author CPU runs and independent scalar checks, not human classroom trial',boundaries=boundaries(),data=data_audit(),experiments=[])
    with tempfile.TemporaryDirectory(prefix='ml09-14-validation-') as temporary:
        tmp=Path(temporary)
        # Every shipped student default is actually executed, with a fresh output folder.
        for n in range(9,15):
            out=tmp/f'lesson-{n}';cmd=[sys.executable,str(STUDENT/f'lesson-{n:02d}/analysis.py'),'--output',str(out)];start=time.perf_counter();r=subprocess.run(cmd,cwd=STUDENT,text=True,capture_output=True,timeout=60);require(r.returncode==0,r.stderr);evidence['experiments'].append(dict(name=f'lesson-{n}-default',seconds=time.perf_counter()-start,summary=read(out/'summary.json')))
        out=tmp/'bike-comparison';start=time.perf_counter();r=subprocess.run([sys.executable,str(STUDENT/'lesson-09/analysis.py'),'--compare','--output',str(out)],text=True,capture_output=True,timeout=60);require(r.returncode==0,r.stderr)
        computed=defaultdict(list)
        for row in rows(out/'records.csv'):computed[row['method']].append(abs(float(row['actual'])-float(row['prediction'])))
        for method,errors in computed.items():require(abs(sum(errors)/len(errors)-read(out/'summary.json')['mae'][method])<1e-8,'bike independent MAE')
        evidence['experiments'].append(dict(name='lesson-09-linear-vs-tree',seconds=time.perf_counter()-start,summary=read(out/'summary.json')))
        configurations=[('manual',dict(representation='manual')),('manual-threshold',dict(representation='manual',threshold=.3)),('bow',dict(representation='bow')),('tfidf',dict(representation='tfidf')),('lr-small',dict(representation='manual',lr=.2)),('lr200-reference',dict(representation='manual',lr=200.,steps=400)),('pretrained',dict(representation='pretrained')),('tfidf-more-steps',dict(representation='tfidf',steps=800)),('tfidf-short-reference',dict(representation='tfidf',lr=.2,steps=100))]
        for name,cfg in configurations:
            out=tmp/name;summary=m.run(cfg,out);audit=scalar_recompute(out);curve=rows(out/'curve.csv');evidence['experiments'].append(dict(name=name,summary=summary,independent=audit,objective_first=float(curve[0]['train_objective']),objective_last=float(curve[-1]['train_objective']),increasing_steps=sum(float(b['train_objective'])>float(a['train_objective']) for a,b in zip(curve,curve[1:]))))
            # Small teacher evidence retained; full reference is reproducible, not duplicated source data.
            teacher=ROOT/'course-instructor/resources/sms/reference'/name;teacher.mkdir(parents=True,exist_ok=True)
            for file in ('summary.json','curve.csv','first_update.json','prediction_trace.json'): (teacher/file).write_bytes((out/file).read_bytes())
        # Same probabilities across threshold-only comparison and same representations across LR.
        require(np.array_equal(np.load(tmp/'manual/model.npz')['w'],np.load(tmp/'manual-threshold/model.npz')['w']),'threshold must not train')
        require((tmp/'manual/representation.json').read_bytes()==(tmp/'lr-small/representation.json').read_bytes(),'LR changed representation')
        # Final gate uses an a priori smoke-test system, never chooses by final outcome.
        lockmod=module(STUDENT/'scripts/lock_sms.py','lock_sms');final=module(ROOT/'course-instructor/scripts/final_sms.py','final_sms')
        selected=tmp/'selected';lockmod.lock(tmp/'manual',selected,'Author protocol smoke test: manual baseline fixed before final read, no tuning on result')
        original=(selected/'config.json').read_bytes();(selected/'config.json').write_bytes(original+b' ');rejects(lambda:final.evaluate(selected),'tampered selected config accepted');(selected/'config.json').write_bytes(original)
        result=final.evaluate(selected);require(result['metrics']['n']==890,'final row count');rejects(lambda:final.evaluate(selected),'repeated final overwrite')
        evidence['final_gate']=dict(fixed_system='manual baseline, a priori smoke test only',n=890,tamper_rejected=True,repeat_rejected=True,metrics_not_exposed_or_used_for_tuning=True,note='Author tested final path once; students do not receive teacher holdout or author final scores. Public-data protocol is not security.')
        # Encode new inputs on CPU, including empty and long text; verify input mutation changes actual vector.
        start=time.perf_counter();encoder=Encoder();loaded=time.perf_counter();texts=['Meeting moved to noon','Meeting cancelled, no reply needed','','hello '*300];x=encoder.encode(texts);elapsed=time.perf_counter()-loaded;require(x.shape==(4,384) and np.isfinite(x).all(),'new encoding shape/finite');require(not np.allclose(x[0],x[1]),'real input sensitivity');require(np.array_equal(x,encoder.encode(texts)),'encoder repeatability')
        evidence['fresh_encoding']=dict(n=4,dimension=384,load_seconds=loaded-start,encode_seconds=elapsed,empty_and_long_inputs_finite=True,input_change_affects_vector=True,encoder_manifest_sha256=m.digest(m.DATA/'encoder/manifest.json'))
    evidence['max_rss_mib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
    m.save_json(destination,evidence);print(json.dumps({k:v for k,v in evidence.items() if k!='experiments'},ensure_ascii=False,indent=2));return evidence
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'validation/lessons09-14/runtime.json');a=p.parse_args();run_checks(a.output)
