"""Optional teacher plots from real training CSVs; matplotlib only for authoring."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]/'course-instructor/resources/sms'
fig,axes=plt.subplots(1,3,figsize=(13,3.8),layout='constrained')
for ax,name,title in zip(axes,['manual','tfidf','lr200-reference'],['Manual features: stable run','TF-IDF: fixed 400-step budget','Manual: large-step reference']):
 with (R/'reference'/name/'curve.csv').open() as f:rows=list(csv.DictReader(f))
 steps=[int(r['step']) for r in rows]
 for key,label in [('train_objective','Train objective (+L2)'),('train_bce','Train BCE'),('dev_bce','Development BCE')]:ax.plot(steps,[float(r[key]) for r in rows],label=label,linewidth=1.5)
 ax.set(xlabel='Full-batch updates',ylabel='Loss per example',title=title);ax.grid(alpha=.2)
axes[0].legend(fontsize=8)
fig.savefig(R/'figures/training-curves.png',dpi=150)
fig.savefig(R/'figures/training-curves.svg')
