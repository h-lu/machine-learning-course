"""S14：用可查看中间数值的微型注意力检查因果遮罩。"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(path): return json.loads(path.read_text(encoding="utf-8"))
def softmax(values):
    largest=max(values); exps=[math.exp(v-largest) for v in values]; total=sum(exps); return [v/total for v in exps]
def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
def attend(row,causal,replacement_position=None,replacement_value=None):
    target=row['target_position']; query=row['query']; visible=[]
    for token in row['tokens']:
        if not causal or token['position']<=target:
            value=replacement_value if token['position']==replacement_position else token['value']
            visible.append((token,query*token['key'],value))
    weights=softmax([x[1] for x in visible]); output=sum(weight*x[2] for weight,x in zip(weights,visible,strict=True))
    return output,[{'position':x[0]['position'],'token':x[0]['token'],'score':x[1],'weight':weight,'value_used':x[2]} for weight,x in zip(weights,visible,strict=True)]
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--config',type=Path,default=HERE/'config.json'); p.add_argument('--data',type=Path,default=HERE/'data/base.json'); p.add_argument('--output',type=Path,default=HERE/'artifacts'); a=p.parse_args()
    data,config=load(a.data),load(a.config); pos=int(config['changed_future_position']); new=float(config['changed_future_value'])
    visibility=[]; weights=[]
    for row in data['rows']:
        if pos<=row['target_position']: raise SystemExit('changed_future_position 必须在目标位置之后，才能检查未来信息。')
        for causal,name in [(True,'causal_mask'),(False,'no_mask')]:
            before,before_weights=attend(row,causal); after,after_weights=attend(row,causal,pos,new)
            visibility.append({'id':row['id'],'condition':name,'target_position':row['target_position'],'changed_position':pos,'before_output':before,'after_output':after,'absolute_change':abs(after-before)})
            for phase,items in [('before',before_weights),('after',after_weights)]:
                for item in items: weights.append({'id':row['id'],'condition':name,'phase':phase,**item})
    a.output.mkdir(parents=True,exist_ok=True); write_csv(a.output/'visibility.csv',visibility); write_csv(a.output/'attention_weights.csv',weights)
    evidence={'product':data['product'],'stage':'S14-information-visibility','evidence_kind':'人工数值表示上的微型注意力机制实验','supports':['因果遮罩使较早位置不能使用未来位置','移除遮罩时未来值可以改变较早位置的数值输出','注意力权重可由分数和 softmax 重算'],'does_not_support':['这些人工数值是真实预训练词元表示','真实大模型一定使用相同权重','数值输出或概率等于事实正确'],'prior_lesson':'S13 区分了输入变化和参数更新；本课只改变信息路径，不训练参数。'}
    (a.output/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary={'lesson':'S14','status':'example_only','config':config,'visibility':visibility,'provenance':{'data_file':a.data.name,'config_file':a.config.name,'data_sha256':hashlib.sha256(a.data.read_bytes()).hexdigest(),'config_sha256':hashlib.sha256(a.config.read_bytes()).hexdigest(),'entry_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},'limits':evidence['does_not_support']}
    (a.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'S14：结果写入 {a.output}。先看 visibility.csv 的 absolute_change，再用 attention_weights.csv 重算一个权重。')
if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as error:
        raise SystemExit(f'无法运行：{error}\n请检查配置、数据字段和 JSON 格式；旧输出不能作为本次运行结果。') from None
