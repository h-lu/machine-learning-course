"""Small readable regression/tree comparison, same train rows and numeric inputs."""
import numpy as np
FIELDS=('hr','workingday','temp','hum','windspeed')
def matrix(rows,fields=FIELDS):
    if not fields or any(f not in FIELDS for f in fields):raise ValueError('Use permitted same-hour numeric information only')
    return np.array([[r[f] for f in fields] for r in rows],dtype=float)
def tree_fit(x,y,depth=2,min_leaf=40):
    node=dict(prediction=float(np.mean(y)),n=len(y))
    if depth==0 or len(y)<2*min_leaf:return node
    best=None
    for feature in range(x.shape[1]):
        for threshold in np.unique(np.quantile(x[:,feature],np.linspace(.05,.95,19))):
            mask=x[:,feature]<=threshold
            if min(mask.sum(),(~mask).sum())<min_leaf:continue
            error=float(((y[mask]-y[mask].mean())**2).sum()+((y[~mask]-y[~mask].mean())**2).sum())
            if best is None or error<best[0]:best=(error,feature,float(threshold),mask)
    if best is None:return node
    _,feature,threshold,mask=best
    node.update(feature=feature,threshold=threshold,left=tree_fit(x[mask],y[mask],depth-1,min_leaf),right=tree_fit(x[~mask],y[~mask],depth-1,min_leaf));return node
def tree_predict(node,row):
    path=[]
    while 'feature' in node:
        left=row[node['feature']]<=node['threshold'];path.append(dict(feature=node['feature'],value=float(row[node['feature']]),threshold=node['threshold'],branch='left' if left else 'right'));node=node['left' if left else 'right']
    return node['prediction'],path+[dict(leaf_n=node['n'],leaf_mean=node['prediction'])]
def compare(train,dev,fields=FIELDS,depth=2,trace_index=0):
    if not isinstance(trace_index,int) or not 0<=trace_index<len(dev):raise ValueError('Trace index must identify a development row')
    if not isinstance(depth,int) or not 1<=depth<=5:raise ValueError('Choose depth 1–5 for the shallow-tree comparison')
    x,dx=matrix(train,fields),matrix(dev,fields);y=np.array([r['cnt'] for r in train]);dy=np.array([r['cnt'] for r in dev]);mean=x.mean(0);std=x.std(0);std[std<1e-12]=1
    a=np.column_stack([np.ones(len(x)),(x-mean)/std]);da=np.column_stack([np.ones(len(dx)),(dx-mean)/std]);w=np.linalg.lstsq(a,y,rcond=None)[0];tree=tree_fit(x,y,depth)
    pred=dict(linear=da@w,shallow_tree=np.array([tree_predict(tree,row)[0] for row in dx]))
    trace=dict(instant=dev[trace_index]['instant'],raw=dx[trace_index].tolist(),fields=list(fields),linear_columns=['intercept']+list(fields),train_mean=mean.tolist(),train_scale=std.tolist(),standardized=da[trace_index].tolist(),coefficients=w.tolist(),contributions=(da[trace_index]*w).tolist(),linear_prediction=float(pred['linear'][trace_index]),tree=tree_predict(tree,dx[trace_index]),tree_model=tree,linear_interpretation='each standardized input contributes additively; no interaction in this model')
    return pred,trace,{name:float(np.mean(np.abs(v-dy))) for name,v in pred.items()}
