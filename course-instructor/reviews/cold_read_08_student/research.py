"""个人单因素实验：全局训练均值与预先固定时段均值。"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.bike_starter import load_development, load_selected_test, write_csv


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n',encoding='utf-8')


def window(hr, config):
    for item in config['windows']:
        if item['start'] <= hr < item['end']:
            return item['name']
    raise ValueError('hour not covered')


def fit(train, config):
    rules = {'baseline': {'n': len(train), 'total': sum(r['cnt'] for r in train)}}
    rules['baseline']['mean'] = rules['baseline']['total']/rules['baseline']['n']
    for item in config['windows']:
        members = [r for r in train if window(r['hr'], config) == item['name']]
        rules[item['name']] = {'n':len(members),'total':sum(r['cnt'] for r in members)}
        rules[item['name']]['mean'] = rules[item['name']]['total']/rules[item['name']]['n']
    return rules


def predict(row, method, rules, config):
    return rules['baseline' if method == 'baseline' else window(row['hr'], config)]['mean']


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output')
    parser.add_argument('--split', choices=['validation','test'],default='validation')
    parser.add_argument('--decision')
    parser.add_argument('--selected-method',choices=['baseline','window_mean'])
    args=parser.parse_args()
    config=json.loads((ROOT/'lesson-08/personal-config.json').read_text())
    plan=ROOT/'lesson-08/plan.md'
    if not plan.is_file() or not plan.read_text().strip():
        raise ValueError('save plan before validation')
    train, validation, audit=load_development(ROOT)
    if args.split=='test':
        if os.getenv('ML08_FORBID_TEST') == '1':
            raise ValueError('CI must not open test')
        if not args.output or not args.decision or not args.selected_method:
            raise ValueError('test requires explicit output, saved decision, selected method')
        decision=ROOT/args.decision
        choice=json.loads(decision.read_text())
        if choice['selected_method'] != args.selected_method:
            raise ValueError('choice differs from saved decision')
        if choice['config_sha256'] != hashlib.sha256((ROOT/'lesson-08/personal-config.json').read_bytes()).hexdigest():
            raise ValueError('config changed after decision')
        evaluation=load_selected_test(ROOT,args.decision)
        methods=[args.selected_method]
    else:
        if args.decision or args.selected_method:
            raise ValueError('validation does not accept test selection')
        evaluation=validation
        methods=['baseline','window_mean']
    output=(ROOT/args.output).resolve() if args.output else ROOT/'lesson-08/artifacts/personal-validation'
    if not output.is_relative_to(ROOT):
        raise ValueError('output outside student repository')
    if args.output and output.exists():
        raise ValueError('explicit output must be new')
    output.mkdir(parents=True,exist_ok=True)
    rules=fit(train,config)
    records=[]
    for method in methods:
        for row in evaluation:
            predicted=predict(row,method,rules,config)
            records.append({'datetime':row['datetime'],'split':args.split,'hr':row['hr'],
              'workingday':row['workingday'],'weathersit':row['weathersit'],'mnth':row['mnth'],
              'window':window(row['hr'],config),'cnt':row['cnt'],'method':method,'prediction':predicted,
              'err_signed':predicted-row['cnt'],'err_absolute':abs(predicted-row['cnt'])})
    groups=[]
    for method in methods:
        for dimension, names in [('overall',['all']),('window',[x['name'] for x in config['windows']]),
                                 ('weather',[str(i) for i in range(1,5)])]:
            for name in names:
                subset=[r for r in records if r['method']==method and (dimension=='overall' or
                  (r['window']==name if dimension=='window' else str(r['weathersit'])==name))]
                groups.append({'dimension':dimension,'group':name,'method':method,'n':len(subset),
                  'mae':sum(r['err_absolute'] for r in subset)/len(subset) if subset else None,
                  'bias':sum(r['err_signed'] for r in subset)/len(subset) if subset else None,
                  'status':'ok' if subset else 'unavailable'})
    comparison=[{'split':args.split,'method':method,'n':len(evaluation),
      'overall_mae':next(g['mae'] for g in groups if g['method']==method and g['dimension']=='overall'),
      'night_n':next(g['n'] for g in groups if g['method']==method and g['group']=='night'),
      'night_mae':next(g['mae'] for g in groups if g['method']==method and g['group']=='night')} for method in methods]
    write_csv(output/'comparison.csv',comparison)
    write_csv(output/'records.csv',records)
    write_csv(output/'group_metrics.csv',groups)
    # 独立核算使用这些记录，不以它自动输出结论。
    sample=[r for r in records if r['method']=='window_mean' and r['hr']<6][:5]
    write_csv(output/'night_five.csv',sample,fieldnames=list(records[0]))
    dump(output/'learned_rules.json',rules)
    dump(output/'data_audit.json',audit)
    dump(output/'config-used.json',config)
    dump(output/'summary.json',{'training_n':len(train),'evaluation_n':len(evaluation),'split':args.split,
        'methods':methods,'metrics':comparison,'data_sha256':audit['data_sha256'],
        'plan_sha256':hashlib.sha256(plan.read_bytes()).hexdigest(),
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'unit':'次租借/已记录小时','test_used_for_selection':False})
    print(json.dumps(comparison,ensure_ascii=False))

if __name__=='__main__':
    main()
