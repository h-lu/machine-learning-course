"""S08：核对预测概率，并比较阈值与固定人工复核名额。"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
HERE = Path(__file__).resolve().parent

def metrics(records, selected):
    tp = sum((r['id'] in selected and r['needs_review'] == 1 for r in records))
    fp = sum((r['id'] in selected and r['needs_review'] == 0 for r in records))
    fn = sum((r['id'] not in selected and r['needs_review'] == 1 for r in records))
    return {'selected_count': len(selected), 'true_positive': tp, 'false_positive': fp, 'false_negative': fn, 'precision': round(tp / (tp + fp), 6) if tp + fp else 0.0, 'recall': round(tp / (tp + fn), 6) if tp + fn else 0.0}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', default=str(HERE / 'config.json'))
    p.add_argument('--output', default=str(HERE / 'artifacts'))
    p.add_argument('--split')
    a = p.parse_args()
    c = json.loads(Path(a.config).read_text(encoding='utf-8'))
    split = a.split or c['evaluation_split']
    if split not in {'validation', 'test'}:
        raise ValueError('evaluation_split 只能是 validation 或 test')
    records = [r for r in json.loads((HERE / 'data/base.json').read_text(encoding='utf-8'))['records'] if r['split'] == split]
    thresholds = {'original_threshold': float(c['original_threshold']), 'candidate_threshold': float(c['candidate_threshold'])}
    if any((t < 0 or t > 1 for t in thresholds.values())):
        raise ValueError('概率阈值必须在 0 到 1 之间')
    policies = []
    selections = {}
    for name, t in thresholds.items():
        selected = {r['id'] for r in records if r['prepared_probability'] >= t}
        selections[name] = selected
        policies.append({'policy': name, 'rule': f'probability >= {t}', **metrics(records, selected)})
    capacity = int(c['review_capacity'])
    if capacity < 1 or capacity > len(records):
        raise ValueError('review_capacity 必须在 1 到评价记录数之间')
    ranked = sorted(records, key=lambda r: (-r['prepared_probability'], r['id']))
    cap = {r['id'] for r in ranked[:capacity]}
    selections['capacity_top_k'] = cap
    policies.append({'policy': 'capacity_top_k', 'rule': f'top {capacity}', **metrics(records, cap)})
    calibration = []
    for low, high in [(0, 0.4), (0.4, 0.7), (0.7, 1.000001)]:
        items = [r for r in records if low <= r['prepared_probability'] < high]
        calibration.append({'probability_bin': f"[{low:.1f}, {min(high, 1):.1f}{(']' if high > 1 else ')')}", 'count': len(items), 'mean_predicted_probability': round(sum((r['prepared_probability'] for r in items)) / len(items), 6) if items else None, 'observed_positive_rate': round(sum((r['needs_review'] for r in items)) / len(items), 6) if items else None})
    rows = [{'id': r['id'], 'split': split, 'probability': r['prepared_probability'], 'actual_needs_review': r['needs_review'], 'original_selected': r['id'] in selections['original_threshold'], 'candidate_selected': r['id'] in selections['candidate_threshold'], 'capacity_selected': r['id'] in cap} for r in ranked]
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=True)
    for name, items in [('comparison.csv', policies), ('calibration.csv', calibration), ('records.csv', rows)]:
        with (out / name).open('w', newline='', encoding='utf-8') as h:
            w = csv.DictWriter(h, fieldnames=list(items[0]))
            w.writeheader()
            w.writerows(items)
    (out / 'summary.json').write_text(json.dumps({'evaluation_split': split, 'sample_count': len(records), 'positive_count': sum((r['needs_review'] for r in records)), 'policies': policies, 'calibration': calibration, 'note': '固定概率来自课前准备的同一模型输出；本课只评价概率和提醒办法，没有重新训练模型。'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('S08 完成：先看 calibration.csv 的人数、平均概率和实际比例，再看 comparison.csv。')
    print(f'结果写入：{out}')
if __name__ == '__main__':
    main()
