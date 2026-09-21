"""S16：可修改、可运行的关键词检索与证据式回答流程。"""
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(path): return json.loads(path.read_text(encoding='utf-8'))
def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as s:
        w=csv.DictWriter(s,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--config',type=Path,default=HERE/'config.json'); p.add_argument('--data',type=Path,default=HERE/'data/base.json'); p.add_argument('--output',type=Path,default=HERE/'artifacts'); a=p.parse_args()
    data,config=load(a.data),load(a.config); split=config['evaluation_split']; queries=[q for q in data['queries'] if q['split']==split]; docs=data['documents']; threshold=int(config['min_overlap']); top_k=int(config['top_k'])
    if split not in {'development','final'} or not queries:
        raise SystemExit('evaluation_split 应为 development 或 final，且 --data 必须包含对应查询。development 用 data/base.json，final 用 data/final.json。')
    if threshold<1 or not 1<=top_k<=len(docs): raise SystemExit('min_overlap 至少为 1；top_k 应在文档数量范围内。')
    retrieval=[]; answers=[]; checks=[]
    for q in queries:
        ranked=[]
        for doc in docs:
            matches=[term for term in q['search_terms'] if term in doc['text']]
            ranked.append((len(matches),doc,matches))
        ranked.sort(key=lambda x:(-x[0],x[1]['id'])); selected=[item for item in ranked[:top_k] if item[0]>=threshold]
        for rank,(score,doc,matches) in enumerate(ranked[:top_k],1): retrieval.append({'query_id':q['id'],'rank':rank,'document_id':doc['id'],'overlap_count':score,'matched_terms':'|'.join(matches),'selected':score>=threshold})
        if not selected:
            answer='现有资料不足，无法回答。'; source=''; extracted=''; retrieved=''
        else:
            score,doc,matches=selected[0]; retrieved=doc['id']
            units=doc['units']; extracted=max(units,key=lambda unit:sum(term in unit for term in q['search_terms']))
            answer=f"{extracted}（来源：{doc['id']}）"; source=doc['id']
        expected=q['expected_document']; retrieval_ok=(retrieved==expected) if expected else (not retrieved)
        answer_supported=(not retrieved and not expected) or (bool(retrieved) and extracted in next(d['text'] for d in docs if d['id']==retrieved))
        task_ok=(q['expected_answer'] in answer) if q['expected_answer'] else ('资料不足' in answer)
        answers.append({'query_id':q['id'],'question':q['question'],'retrieved_document':retrieved,'answer':answer,'expected_document':expected,'retrieval_ok':retrieval_ok,'answer_supported':answer_supported,'task_ok':task_ok})
        checks.append({'query_id':q['id'],'retrieval_success':retrieval_ok,'generation_supported':answer_supported,'task_complete':task_ok,'failure_stage':'retrieval' if not retrieval_ok else ('answer' if not task_ok else 'none')})
    a.output.mkdir(parents=True,exist_ok=True); write_csv(a.output/'retrieval.csv',retrieval); write_csv(a.output/'answers.csv',answers); write_csv(a.output/'checks.csv',checks)
    evidence={'product':data['product'],'stage':'S16-retrieval-and-support','evidence_kind':'动态关键词检索 + 从检索文档逐字抽取的本地回答','supports':['修改查询词或资料后会重新检索并生成匹配的新结果','检索是否找到正确资料与回答是否受资料支持可以分开检查','资料不足时可以停止回答'],'does_not_support':['关键词重合等于语义相关','本地抽取器代表真实大语言模型生成能力','引用了文档就保证回答满足问题'],'prior_lesson':'S15 改了任务说明；本课保持回答规则简单，重点检查外部资料是否找到并真正支持输出。'}
    (a.output/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary={'lesson':'S16','status':'example_only','config':config,'n_queries':len(queries),'retrieval_rate':sum(r['retrieval_ok'] for r in answers)/len(answers),'task_rate':sum(r['task_ok'] for r in answers)/len(answers),'provenance':{'data_file':a.data.name,'config_file':a.config.name,'data_sha256':hashlib.sha256(a.data.read_bytes()).hexdigest(),'config_sha256':hashlib.sha256(a.config.read_bytes()).hexdigest(),'entry_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},'limits':evidence['does_not_support']}
    (a.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"S16：处理 {len(queries)} 条 {split} 查询。先看 retrieval.csv，再看 answers.csv 与 checks.csv。")
if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as error:
        raise SystemExit(f'无法运行：{error}\n请检查配置、数据字段和 JSON 格式；旧输出不能作为本次运行结果。') from None
