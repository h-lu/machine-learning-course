"""Compare two saved training conditions that differ only in lr or steps."""
from pathlib import Path
import argparse,csv,json

def compare(first,second,output):
    def load(p,n):return json.loads((p/n).read_text())
    c1,c2=load(first,'config.json'),load(second,'config.json')
    changed=[k for k in c1.keys()|c2.keys() if c1.get(k)!=c2.get(k)]
    if changed not in [['lr'],['steps']]:raise ValueError('这份比较工具要求只改变lr或只改变steps，其他配置保持相同')
    if load(first,'representation.json')!=load(second,'representation.json'):raise ValueError('两方案表示并未固定')
    summaries=[load(p,'summary.json') for p in [first,second]]
    for key in ['train_ids_sha256','dev_ids_sha256','train_data_sha256','dev_data_sha256']:
        if summaries[0][key]!=summaries[1][key]:raise ValueError('数据划分不一致')
    if output.exists():raise FileExistsError('比较输出已存在，请用新文件名')
    result=[]
    for name,p,c,s in zip(['first','second'],[first,second],[c1,c2],summaries):
        with (p/'curve.csv').open(newline='') as f:curve=list(csv.DictReader(f))
        end=curve[-1];m=s['metrics']
        result.append(dict(scheme=name,changed=changed[0],lr=c['lr'],steps=c['steps'],train_objective=float(end['train_objective']),train_bce=float(end['train_bce']),dev_bce=float(end['dev_bce']),tp=m['tp'],fp=m['fp'],fn=m['fn'],tn=m['tn'],precision=m['precision'],recall=m['recall'],tracked_id='sms-00004',tracked_probability=float(end['tracked_dev_probability'])))
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]),lineterminator='\n');w.writeheader();w.writerows(result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--first',type=Path,required=True);p.add_argument('--second',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:compare(a.first,a.second,a.output)
    except (OSError,ValueError,KeyError) as e:p.exit(1,str(e)+'\n')
