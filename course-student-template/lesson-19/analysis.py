"""S17：在同一批固定候选输出上比较提示、上下文和参数适配路线。"""
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
    data,config=load(a.data),load(a.config); routes=config['routes']
    if not isinstance(routes,list) or len(routes)!=2 or len(set(routes))!=2: raise SystemExit('routes 必须列出两个不同候选。')
    metadata={r['id']:r for r in data['routes']}
    if any(route not in metadata for route in routes): raise SystemExit('候选路线不存在；固定材料只覆盖 data/base.json 中列出的路线。')
    cases=[]; comparison=[]
    for route in routes:
        totals={'task':0,'support':0,'format':0}
        for case in data['cases']:
            if route not in case['outputs']: raise SystemExit(f"{case['id']} 缺少 {route} 的匹配输出；不能套用别的缓存。")
            output=case['outputs'][route]; answerable=bool(case['expected_answer'])
            task=(case['expected_answer'] in output) if answerable else ('资料不足' in output)
            support=(case['required_source'] in output) if answerable else ('资料不足' in output)
            formatted=('结论：' in output and ('来源' in output or not answerable))
            totals['task']+=task; totals['support']+=support; totals['format']+=formatted
            cases.append({'route':route,'case_id':case['id'],'question':case['question'],'output':output,'task_ok':task,'support_ok':support,'format_ok':formatted})
        m=metadata[route]; n=len(data['cases'])
        comparison.append({'route':route,'n':n,'task_rate':totals['task']/n,'support_rate':totals['support']/n,'format_rate':totals['format']/n,'parameters_updated':m['parameters_updated'],'extra_documents':m['extra_documents'],'adaptation_examples':m['adaptation_examples'],'setup_minutes':m['setup_minutes'],'fixed_material_only':True})
    a.output.mkdir(parents=True,exist_ok=True); write_csv(a.output/'route_comparison.csv',comparison); write_csv(a.output/'case_scores.csv',cases)
    evidence={'product':data['product'],'stage':'S17-route-choice','evidence_kind':'有来源的固定候选输出，只覆盖三条已准备路线和当前六个案例','supports':['在完全相同的案例和评分规则下比较两条路线','提示、上下文和参数适配改变的环节及维护成本不同','分数与成本可以共同支持采用或保留决定'],'does_not_support':['学生自写的新提示已经产生过输出','固定 parameter_adapter 输出证明真实参数训练效果','当前最佳路线适合其他数据或全部大模型'],'prior_lessons':'S15 练习提示开发，S16 练习检索；本课在同一用途下选择适配位置。'}
    (a.output/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary={'lesson':'S17','status':'example_only','config':config,'comparison':comparison,'provenance':{'data_file':a.data.name,'config_file':a.config.name,'data_sha256':hashlib.sha256(a.data.read_bytes()).hexdigest(),'config_sha256':hashlib.sha256(a.config.read_bytes()).hexdigest(),'entry_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},'limits':evidence['does_not_support']}
    (a.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"S17：已比较 {routes[0]} 与 {routes[1]}。先看 route_comparison.csv，再找 case_scores.csv 中结论相反的案例。")
if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as error:
        raise SystemExit(f'无法运行：{error}\n请检查配置、数据字段和 JSON 格式；旧输出不能作为本次运行结果。') from None
