"""S09：在同一近邻方法下比较原始表示、缩放表示和完整表示。"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
CHANNELS = ['web', 'email', 'phone']

def stats(train):
    result = {}
    for key in ('message_length', 'history_count', 'urgency_count'):
        v = np.array([r[key] for r in train if r[key] is not None], float)
        result[key] = {'mean': float(v.mean()), 'std': float(v.std()) or 1.0, 'median': float(np.median(v))}
    return result

def vector(r, mode, s):
    missing = r['message_length'] is None
    numeric = {'message_length': s['message_length']['median'] if missing else float(r['message_length']), 'history_count': float(r['history_count']), 'urgency_count': float(r['urgency_count'])}
    if mode == 'raw':
        return np.array([numeric['message_length'], numeric['history_count'], numeric['urgency_count'], float(r['attachment_missing'])])
    values = [(numeric[k] - s[k]['mean']) / s[k]['std'] for k in ('message_length', 'history_count', 'urgency_count')] + [float(r['attachment_missing'])]
    if mode == 'prepared':
        values += [float(missing)] + [float(r['channel'] == c) for c in CHANNELS] + [float(r['channel'] not in CHANNELS)]
    return np.array(values, float)

def predict(train, q, mode, s, k):
    v = vector(q, mode, s)
    dist = sorted([(r['id'], float(np.linalg.norm(v - vector(r, mode, s))), int(r['needs_review'])) for r in train], key=lambda x: (x[1], x[0]))[:k]
    return (int(sum((x[2] for x in dist)) * 2 >= k), dist)

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
    k = int(c['neighbors'])
    candidate = c['candidate_representation']
    if k < 1 or k % 2 == 0 or k > 24:
        raise ValueError('neighbors 必须是不超过训练记录数的正奇数')
    if candidate not in {'scaled', 'prepared'}:
        raise ValueError('candidate_representation 只能是 scaled 或 prepared')
    data = json.loads((HERE / 'data/base.json').read_text(encoding='utf-8'))
    train = [r for r in data['records'] if r['split'] == 'train']
    evaluation = [r for r in data['records'] if r['split'] == split]
    s = stats(train)
    modes = ['raw', candidate]
    comparison = []
    rows = []
    for mode in modes:
        correct = 0
        for r in evaluation:
            pred, near = predict(train, r, mode, s, k)
            correct += pred == r['needs_review']
            rows.append({'id': r['id'], 'split': split, 'representation': mode, 'actual': r['needs_review'], 'predicted': pred, 'nearest_ids': '|'.join((x[0] for x in near)), 'nearest_distances': '|'.join((f'{x[1]:.4f}' for x in near))})
        comparison.append({'representation': mode, 'neighbors': k, 'correct': correct, 'sample_count': len(evaluation), 'accuracy': round(correct / len(evaluation), 6)})
    probes = []
    for r in data['challenge_records']:
        for mode in modes:
            pred, near = predict(train, r, mode, s, k)
            probes.append({'id': r['id'], 'note': r['note'], 'representation': mode, 'actual': r['needs_review'], 'predicted': pred, 'nearest_ids': '|'.join((x[0] for x in near))})
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=True)
    for name, items in [('comparison.csv', comparison), ('records.csv', rows), ('challenge.csv', probes)]:
        with (out / name).open('w', newline='', encoding='utf-8') as h:
            w = csv.DictWriter(h, fieldnames=list(items[0]))
            w.writeheader()
            w.writerows(items)
    (out / 'summary.json').write_text(json.dumps({'evaluation_split': split, 'training_count': len(train), 'training_statistics': s, 'comparison': comparison, 'challenge_records': probes, 'note': '所有均值、中位数和标准差只由训练集计算；距离接近不保证标签相同。'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('S09 完成：先看 comparison.csv，再在 challenge.csv 找 P01、P02 和 P03。')
    print(f'结果写入：{out}')
if __name__ == '__main__':
    main()
