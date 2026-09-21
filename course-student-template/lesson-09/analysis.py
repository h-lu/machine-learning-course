"""S07：比较简单模型与复杂模型，并检查训练范围外的预测。"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent

def design(x, degree):
    return np.column_stack([x ** p for p in range(degree + 1)])

def fit(train_x, train_y, degree):
    matrix = design(train_x, degree)
    return np.linalg.lstsq(matrix, train_y, rcond=None)[0]

def mae(actual, predicted):
    return float(np.mean(np.abs(actual - predicted)))

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', default=str(HERE / 'config.json'))
    p.add_argument('--output', default=str(HERE / 'artifacts'))
    p.add_argument('--split')
    a = p.parse_args()
    config = json.loads(Path(a.config).read_text(encoding='utf-8'))
    split = a.split or config['evaluation_split']
    if split not in {'validation', 'test'}:
        raise ValueError('evaluation_split 只能是 validation 或 test')
    data = json.loads((HERE / 'data/base.json').read_text(encoding='utf-8'))
    records = data['records']
    degree = int(config['candidate_degree'])
    if degree not in {2, 3}:
        raise ValueError('candidate_degree 只能是 2 或 3')
    train = [r for r in records if r['split'] == 'train']
    tx = np.array([r['detail_count'] for r in train], float)
    ty = np.array([r['handling_minutes'] for r in train], float)
    models = {'simple_linear': 1, 'candidate_complex': degree}
    weights = {}
    comparison = []
    record_rows = []
    for name, d in models.items():
        coef = fit(tx, ty, d)
        weights[name] = coef
        train_pred = design(tx, d) @ coef
        subset = [r for r in records if r['split'] == split]
        x = np.array([r['detail_count'] for r in subset], float)
        y = np.array([r['handling_minutes'] for r in subset], float)
        pred = design(x, d) @ coef
        row = {'method': name, 'degree': d, 'train_mae_minutes': round(mae(ty, train_pred), 6), 'evaluation_split': split, 'evaluation_mae_minutes': round(mae(y, pred), 6)}
        for source, estimate in zip(subset, pred):
            record_rows.append({'id': source['id'], 'split': split, 'method': name, 'detail_count': source['detail_count'], 'actual_minutes': source['handling_minutes'], 'predicted_minutes': round(float(estimate), 6), 'absolute_error_minutes': round(abs(source['handling_minutes'] - float(estimate)), 6)})
        comparison.append(row)
    outside = float(config['outside_detail_count'])
    train_min, train_max = (float(tx.min()), float(tx.max()))
    probes = []
    for name, d in models.items():
        probes.append({'method': name, 'detail_count': outside, 'predicted_minutes': round((design(np.array([outside]), d) @ weights[name]).item(), 6), 'observed_label': None})
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=True)
    for filename, items in [('comparison.csv', comparison), ('records.csv', record_rows), ('outside_check.csv', probes)]:
        with (out / filename).open('w', newline='', encoding='utf-8') as h:
            w = csv.DictWriter(h, fieldnames=list(items[0]))
            w.writeheader()
            w.writerows(items)
    summary = {'purpose': '预测一条咨询记录需要的处理分钟数', 'train_detail_range': [train_min, train_max], 'evaluation_split': split, 'counts': {'train': len(train), split: len(subset)}, 'comparison': comparison, 'outside_check': {'input': outside, 'outside_training_range': outside < train_min or outside > train_max, 'has_observed_label': False, 'predictions': probes}, 'note': '范围外记录没有真实处理时间，只能显示模型假设分歧，不能判断谁更准。'}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    split_name = '验证集' if split == 'validation' else '测试集'
    print(f'S07 完成：先看 comparison.csv 的训练与{split_name} MAE，再看 outside_check.csv。')
    print(f'结果写入：{out}')
if __name__ == '__main__':
    main()
