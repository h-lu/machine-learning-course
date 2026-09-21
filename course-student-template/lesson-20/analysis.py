"""S18：分维度汇总两位人工评分，并检查分歧与顺序变化。"""
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
DIMS=['task_completion','factuality','evidence_support','format']

def load(path): return json.loads(path.read_text(encoding='utf-8'))
def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as s:
        w=csv.DictWriter(s,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--config',type=Path,default=HERE/'config.json'); p.add_argument('--data',type=Path,default=HERE/'data/base.json'); p.add_argument('--output',type=Path,default=HERE/'artifacts'); a=p.parse_args()
    data,config=load(a.data),load(a.config); split=config['evaluation_split']; order=config['presentation_order']; weights=config['weights']; cases=[c for c in data['cases'] if c['split']==split]
    if split not in {'development','final'} or not cases:
        raise SystemExit('evaluation_split 应为 development 或 final，且 --data 必须包含对应案例。development 用 data/base.json，final 用 data/final.json。')
    if order not in {'AB','BA'} or set(weights)!=set(DIMS) or abs(sum(weights.values())-1)>1e-8: raise SystemExit('presentation_order 应为 AB/BA；四项权重必须齐全且总和为 1。')
    scores=[]; disagreements=[]; pairs=[]
    for case in cases:
        totals={}
        for name,candidate in case['candidates'].items():
            means={dim:(candidate['reviewer_1'][dim]+candidate['reviewer_2'][dim])/2 for dim in DIMS}
            total=sum(means[d]*weights[d] for d in DIMS); totals[name]=total
            row={'case_id':case['id'],'candidate':name,'output':candidate['output'],**{f'{d}_mean':means[d] for d in DIMS},'weighted_total':total,'fixed_proxy_score':candidate[f'proxy_{order}'],'presentation_order':order}
            scores.append(row)
            for dim in DIMS:
                gap=abs(candidate['reviewer_1'][dim]-candidate['reviewer_2'][dim])
                if gap>=config['disagreement_threshold']:
                    disagreements.append({'case_id':case['id'],'candidate':name,'dimension':dim,'reviewer_1':candidate['reviewer_1'][dim],'reviewer_2':candidate['reviewer_2'][dim],'absolute_gap':gap,'action':'查看资料和评分说明后讨论，不用平均数掩盖分歧'})
        winner='tie' if abs(totals['A']-totals['B'])<1e-9 else max(totals,key=totals.get)
        pairs.append({'case_id':case['id'],'candidate_A_total':totals['A'],'candidate_B_total':totals['B'],'human_winner':winner,'difference_A_minus_B':totals['A']-totals['B']})
    if not disagreements: disagreements=[{'case_id':'none','candidate':'none','dimension':'none','reviewer_1':'','reviewer_2':'','absolute_gap':0,'action':'本次没有达到阈值的分歧'}]
    a.output.mkdir(parents=True,exist_ok=True); write_csv(a.output/'dimension_scores.csv',scores); write_csv(a.output/'disagreements.csv',disagreements); write_csv(a.output/'pairwise.csv',pairs)
    evidence={'product':data['product'],'stage':'S18-open-answer-evaluation','evidence_kind':'两位人工评分记录 + 明确标为固定模拟评价器的顺序分数','supports':['开放答案可以按任务完成、事实、资料支持和格式分开评价','评分者分歧需要回看依据，平均数不能解释分歧原因','固定模拟评价器的分数可能随呈现顺序变化'],'does_not_support':['人工平均分是唯一正确答案','固定模拟评价器代表真实 AI 评价能力','开发样本上选出的权重已在最终样本上验证'],'prior_lessons':'S15—S17 形成了候选回答和适配选择；本课只评价这些输出，不反过来让评价器生成答案。'}
    (a.output/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary={'lesson':'S18','status':'example_only','config':config,'n_cases':len(cases),'pairwise':pairs,'provenance':{'data_file':a.data.name,'config_file':a.config.name,'data_sha256':hashlib.sha256(a.data.read_bytes()).hexdigest(),'config_sha256':hashlib.sha256(a.config.read_bytes()).hexdigest(),'entry_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},'limits':evidence['does_not_support']}
    (a.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"S18：汇总 {len(cases)} 个 {split} 案例。先看 dimension_scores.csv，再处理 disagreements.csv。")
if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as error:
        raise SystemExit(f'无法运行：{error}\n请检查配置、数据字段和 JSON 格式；旧输出不能作为本次运行结果。') from None
