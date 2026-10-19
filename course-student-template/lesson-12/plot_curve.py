"""Plot saved training/development BCE on a common scale using SVG (stdlib only)."""
import argparse,csv,math
from pathlib import Path

def draw(run):
    with (run/'curve.csv').open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
    keys=['train_bce','dev_bce'];series=[[float(r[k]) for r in rows] for k in keys]
    if not rows or not all(math.isfinite(v) for vs in series for v in vs):raise ValueError('需要有限的曲线值')
    hi=max(max(vs) for vs in series)*1.05 or 1.;steps=[int(r['step']) for r in rows];end=max(steps) or 1
    s=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="430" viewBox="0 0 900 430">','<rect width="900" height="430" fill="white"/>','<g font-family="sans-serif" font-size="16" fill="#183346">','<text x="60" y="32">训练与开发损失：同为不含正则项的BCE</text>']
    for i in range(5):
        y=350-280*i/4;s+=['<path d="M70 '+str(y)+' H860" stroke="#dde4e8"/>',f'<text x="7" y="{y+5}">{hi*i/4:.3f}</text>']
    for vals,color,label,ylabel in zip(series,['#246cab','#d55e00'],['train_bce','dev_bce'],[65,90]):
        points=' '.join(f'{70+790*t/end:.3f},{350-280*v/hi:.3f}' for t,v in zip(steps,vals));s+=[f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2"/>',f'<text x="660" y="{ylabel}" fill="{color}">{label}</text>']
    s+=['<path d="M70 65 V350 H860" fill="none" stroke="#183346"/>','<text x="65" y="380">0</text>',f'<text x="815" y="380">{max(steps)}</text>','<text x="400" y="412">更新步数（step）</text>','</g></svg>']
    target=run/'loss.svg';target.write_text('\n'.join(s)+'\n',encoding='utf-8');print(target)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args();draw(a.run)
