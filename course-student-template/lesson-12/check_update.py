"""Independently check one coordinate and the bias in the first full-batch update."""
from pathlib import Path
import argparse,json,sys,math,csv
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from mlcourse import sms_course
from mlcourse.text_representations import transform,SparseRows

def check(folder,feature):
    rep=json.loads((folder/'representation.json').read_text());u=json.loads((folder/'first_update.json').read_text())
    names=rep['names'];j=0 if feature is None else names.index(feature)
    rows=sms_course.load_rows('train');x=transform([r['text'] for r in rows],rep)
    w=np.asarray(u['weights_before']);b=u['bias_before'];y=np.array([r['label']=='spam' for r in rows],dtype=float)
    z=(x.matvec(w) if isinstance(x,SparseRows) else x@w)+b
    p=np.exp(-np.logaddexp(0,-z));a=np.where(y==1,u['spam_weight'],1.)
    col=np.zeros(len(rows))
    if isinstance(x,SparseRows):
        for i in range(len(rows)):
            ids,vals=x.row(i)
            for index,value in zip(ids,vals):
                if index==j:col[i]=value;break
    else:col=x[:,j]
    terms=a*(p-y)*col;grad=math.fsum(terms.tolist())/math.fsum(a.tolist())+u['l2']*w[j]
    gb=math.fsum((a*(p-y)).tolist())/math.fsum(a.tolist())
    assert math.isclose(grad,u['gradient_weights'][j],abs_tol=1e-11)
    assert math.isclose(gb,u['gradient_bias'],abs_tol=1e-11)
    neww=w[j]-u['learning_rate']*grad;newb=b-u['learning_rate']*gb
    assert math.isclose(neww,u['weights_after'][j],abs_tol=1e-11)
    result=dict(feature=names[j],training_records=len(rows),training_spam=int(y.sum()),first_train_id=rows[0]['id'],first_train_text=rows[0]['text'],first_train_label=int(y[0]),first_train_x=float(col[0]),first_train_probability=float(p[0]),first_train_unaveraged_term=float(terms[0]),sum_unaveraged_terms=math.fsum(terms.tolist()),denominator=math.fsum(a.tolist()),regularization_term=float(u['l2']*w[j]),gradient=grad,new_weight=float(neww),bias_gradient=gb,new_bias=newb,first_update_verified=True)
    print(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':
    q=argparse.ArgumentParser();q.add_argument('--run',type=Path,required=True);q.add_argument('--feature');args=q.parse_args();check(args.run,args.feature)
