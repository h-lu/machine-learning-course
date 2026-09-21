"""S15：用会接收新提示和新输入的本地模板生成器练习提示比较。"""
from __future__ import annotations
import argparse, csv, hashlib, json, random
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(path): return json.loads(path.read_text(encoding='utf-8'))
def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def prompt_features(prompt):
    """Return the literal switches implemented by this teaching simulator."""
    return {
        'cite_source': '引用来源' in prompt,
        'evidence_first': '先写依据' in prompt,
        'abstain_when_missing': '资料不足' in prompt,
        'structured_conclusion': '结论' in prompt,
    }

def generate(row,prompt,rng):
    features=prompt_features(prompt)
    asks_source=features['cite_source']; evidence_first=features['evidence_first']
    abstain=features['abstain_when_missing']; structured=features['structured_conclusion']
    if not row['evidence']:
        if abstain: return '现有资料不足，无法回答。'
        return rng.choice(['通常可以办理，请再确认。','暂时没有明确限制。','建议按常见做法处理。'])
    if evidence_first:
        return f"依据（{row['source']}）：{row['evidence']}。结论：{row['answer']}。"
    if structured:
        suffix=f" 来源：{row['source']}。" if asks_source else ''
        return f"结论：{row['answer']}。{suffix}"
    return f"{row['answer']}。"
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--config',type=Path,default=HERE/'config.json'); p.add_argument('--data',type=Path,default=HERE/'data/base.json'); p.add_argument('--output',type=Path,default=HERE/'artifacts'); a=p.parse_args()
    data,config=load(a.data),load(a.config); split=config['evaluation_split']; rows=[r for r in data['rows'] if r['split']==split]
    if split not in {'development','final'} or not rows: raise SystemExit('evaluation_split 应为 development 或 final，且 --data 必须包含对应问题。development 用 data/base.json，final 用 data/final.json。')
    repeats=int(config['repeats']);
    if not 1<=repeats<=20: raise SystemExit('repeats 应在 1—20。')
    features=prompt_features(config['prompt_text'])
    if config['prompt_text'].strip() != '请简短回答学生的问题。' and not any(features.values()):
        raise SystemExit('教学生成器没有识别到提示规则。请使用 README 列出的“引用来源”“先写依据”“资料不足”或“结论”中的至少一项。')
    responses=[]; repeat_metrics=[]
    for repeat in range(1,repeats+1):
        rng=random.Random(int(config['seed'])+repeat); totals={'task_ok':0,'citation_ok':0,'format_ok':0,'unsupported_claim':0}
        for row in rows:
            output=generate(row,config['prompt_text'],rng); answerable=bool(row['evidence'])
            task_ok=(row['answer'] in output) if answerable else ('资料不足' in output)
            citation_ok=(row['source'] in output) if answerable else ('资料不足' in output)
            format_ok=('结论：' in output and ('依据（' in output or not answerable)) if '结论' in config['prompt_text'] else True
            unsupported=(not answerable and '资料不足' not in output)
            values={'task_ok':task_ok,'citation_ok':citation_ok,'format_ok':format_ok,'unsupported_claim':unsupported}
            for k,v in values.items(): totals[k]+=int(v)
            responses.append({'repeat':repeat,'id':row['id'],'split':split,'question':row['question'],'answerable':answerable,'output':output,**values})
        repeat_metrics.append({'repeat':repeat,'n':len(rows),'task_rate':totals['task_ok']/len(rows),'citation_rate':totals['citation_ok']/len(rows),'format_rate':totals['format_ok']/len(rows),'unsupported_rate':totals['unsupported_claim']/len(rows)})
    a.output.mkdir(parents=True,exist_ok=True); write_csv(a.output/'responses.csv',responses); write_csv(a.output/'metrics.csv',repeat_metrics)
    (a.output/'prompt_features.json').write_text(json.dumps(features,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    evidence={'product':data['product'],'stage':'S15-prompt-generalization','evidence_kind':'可重新运行的本地规则模板生成器','supports':['每次提示修改都会由程序产生对应的新输出','开发记录可用于选择提示，final 记录应在选择后再看','重复运行可以显示模板中预设的随机措辞差异'],'does_not_support':['该模板生成器代表真实大语言模型能力','开发记录变好保证未参与修改的记录也变好','重复运行增加了独立评价问题的数量'],'prior_lessons':'S13 区分输入与参数变化；S14 说明输入可见性。本课改变任务说明，不更新参数。'}
    (a.output/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary={'lesson':'S15','status':'example_only','config':config,'n_questions':len(rows),'metrics':repeat_metrics,'provenance':{'data_file':a.data.name,'config_file':a.config.name,'data_sha256':hashlib.sha256(a.data.read_bytes()).hexdigest(),'config_sha256':hashlib.sha256(a.config.read_bytes()).hexdigest(),'entry_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},'limits':evidence['does_not_support']}
    (a.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"S15：已在 {split} 的 {len(rows)} 个问题上生成 {repeats} 次结果。先看 responses.csv，再看 metrics.csv。")
if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as error:
        raise SystemExit(f'无法运行：{error}\n请检查配置、数据字段和 JSON 格式；旧输出不能作为本次运行结果。') from None
