"""Two labelled scalar examples: exact full-batch logistic update, no regularization."""
import math,json
from pathlib import Path

def sigmoid(z):return 1/(1+math.exp(-z))
def loss(w,b):return sum(math.log1p(math.exp(w*x+b))-y*(w*x+b) for x,y in [(0.,0.),(2.,1.)])/2

def main():
    data=[(0.,0.),(2.,1.)];w=b=0.;lr=1.
    terms=[dict(x=x,y=y,p=sigmoid(w*x+b),residual=sigmoid(w*x+b)-y,weight_term=(sigmoid(w*x+b)-y)*x) for x,y in data]
    gw=sum(r['weight_term'] for r in terms)/2;gb=sum(r['residual'] for r in terms)/2
    nw,nb=w-lr*gw,b-lr*gb
    result=dict(artificial_example=True,terms=terms,learning_rate=lr,w_before=w,b_before=b,gradient_w=gw,gradient_b=gb,w_after=nw,b_after=nb,loss_before=loss(w,b),loss_after=loss(nw,nb),probabilities_after=[sigmoid(nw*x+nb) for x,y in data])
    out=Path(__file__).parent/'artifacts/small-example.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
