"""One optional teacher reasoning example, not the standard student investigation."""
from pathlib import Path
import sys,os,json,tempfile
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'course-student-template'))
from mlcourse import sms_course as m
if __name__=='__main__':
 out=R/'course-instructor/resources/sms/diagnosis';out.mkdir(parents=True,exist_ok=True)
 # Choose slice and predictions before running either comparison; no final data loaded.
 plan=dict(slice='dev spam messages with <=12 tokenizer tokens',explanation_a='400 updates may leave the fixed TF-IDF head under-trained',explanation_b='the selected short messages may be all OOV, so this representation provides no input signal',experiment='fixed representation/settings; 400 vs 800 updates; examine nonzero count and per-ID probability, not only total accuracy',prediction_a='training loss and some missed probabilities should improve with more updates',prediction_b='all-zero representations share intercept-only scores and adding updates cannot separate their texts',primary='same short-spam IDs: recall at fixed threshold 0.5; also examine vector nonzero counts',controls='same train/dev IDs, vocabulary/IDF, L2=.001, uniform weights, initialization, lr=1, threshold=.5, capacity=1')
 m.save_json(out/'plan.json',plan)
 train,dev=m.load_rows('train'),m.load_rows('dev');rep=m.fit_representation([r['text'] for r in train],'tfidf');x=m.transform([r['text'] for r in dev],rep)
 selected=[i for i,r in enumerate(dev) if r['label']=='spam' and len(m.tokens(r['text']))<=12]
 with tempfile.TemporaryDirectory() as temp:
  results=[]
  for steps in (400,800):
   p=Path(temp)/str(steps);s=m.run(dict(representation='tfidf',lr=1.,steps=steps),p);model=np.load(p/'model.npz');prob=m.sigmoid(x@model['w']+model['b']);results.append((prob,s))
  table=[dict(id=dev[i]['id'],label='spam',token_count=len(m.tokens(dev[i]['text'])),nonzero=int(np.count_nonzero(x[i])),p400=float(results[0][0][i]),p800=float(results[1][0][i]),selected400=bool(results[0][0][i]>=.5),selected800=bool(results[1][0][i]>=.5)) for i in selected]
  m.write_csv(out/'short-spam.csv',table)
  misses=[r for r in table if not r['selected400']];example=misses[0] if misses else table[0]
  summary=dict(rows=len(table),zero_vectors=sum(r['nonzero']==0 for r in table),recall400=sum(r['selected400'] for r in table)/len(table),recall800=sum(r['selected800'] for r in table)/len(table),example=example,final_test_opened=False,conclusion='No all-OOV vector would weaken explanation B for this slice; any probability/recall improvement supports A partially, but does not establish sufficient semantic representation or unique cause. The candidate can still be rejected for cost or remaining misses.')
  m.save_json(out/'summary.json',summary);print(json.dumps(summary,indent=2))
