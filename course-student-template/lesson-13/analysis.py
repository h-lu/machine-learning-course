"""S11：比较原始特征与从另一批无标签数据学习后冻结的表示。"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
FEATURES = ['message_length', 'history_count', 'urgency_count', 'attachment_missing']

def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -30, 30)))

def fit(x, y, epochs=300, rate=0.15, reg=0.02):
    x = np.column_stack([np.ones(len(x)), x])
    w = np.zeros(x.shape[1])
    for _ in range(epochs):
        p = sigmoid(x @ w)
        g = x.T @ (p - y) / len(y)
        g[1:] += reg * w[1:]
        w -= rate * g
    return w

def evaluate(x, y, w):
    p = sigmoid(np.column_stack([np.ones(len(x)), x]) @ w)
    return (float(np.mean((p >= 0.5) == y)), p)

def raw_rep(records, mean, std):
    return (np.array([[r[k] for k in FEATURES] for r in records], float) - mean) / std

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
    dim = int(c['borrowed_dimensions'])
    if dim not in {1, 2, 3}:
        raise ValueError('borrowed_dimensions 只能是 1、2 或 3')
    data = json.loads((HERE / 'data/base.json').read_text(encoding='utf-8'))
    source = np.array([[r[k] for k in FEATURES] for r in data['source_unlabeled']], float)
    source_mean = source.mean(0)
    source_std = source.std(0)
    source_std[source_std == 0] = 1
    source_scaled = (source - source_mean) / source_std
    cov = np.cov(source_scaled, rowvar=False)
    values, vectors = np.linalg.eigh(cov)
    order = np.argsort(values)[::-1]
    components = vectors[:, order[:dim]]
    target = data['target_records']
    train = [r for r in target if r['split'] == 'train']
    evaluation = [r for r in target if r['split'] == split]
    y = np.array([r['needs_review'] for r in train], float)
    ey = np.array([r['needs_review'] for r in evaluation], float)
    target_raw = np.array([[r[k] for k in FEATURES] for r in train], float)
    tm = target_raw.mean(0)
    ts = target_raw.std(0)
    ts[ts == 0] = 1
    representations = {'raw_target_scaled': (raw_rep(train, tm, ts), raw_rep(evaluation, tm, ts)), 'borrowed_frozen': ((target_raw - source_mean) / source_std @ components, (np.array([[r[k] for k in FEATURES] for r in evaluation], float) - source_mean) / source_std @ components)}
    comparison = []
    rows = []
    models = {}
    for name, (tx, ex) in representations.items():
        w = fit(tx, y)
        models[name] = (w, tx, ex)
        ta, _ = evaluate(tx, y, w)
        ea, probs = evaluate(ex, ey, w)
        comparison.append({'representation': name, 'dimensions': tx.shape[1], 'train_accuracy': round(ta, 6), 'evaluation_accuracy': round(ea, 6)})
        for record, prob in zip(evaluation, probs):
            rows.append({'id': record['id'], 'split': split, 'representation': name, 'actual': record['needs_review'], 'probability': round(float(prob), 8), 'predicted': int(prob >= 0.5)})
    feature = c['stress_feature']
    if feature not in FEATURES:
        raise ValueError('stress_feature 必须是已列出的特征')
    stressed = [dict(r) for r in evaluation]
    replacement = float(np.mean([r[feature] for r in train]))
    for r in stressed:
        r[feature] = replacement
    stress = []
    for name, (w, _, _) in models.items():
        if name == 'raw_target_scaled':
            sx = raw_rep(stressed, tm, ts)
        else:
            sx = (np.array([[r[k] for k in FEATURES] for r in stressed], float) - source_mean) / source_std @ components
        acc, _ = evaluate(sx, ey, w)
        stress.append({'representation': name, 'changed_feature': feature, 'replacement': round(replacement, 6), 'stressed_accuracy': round(acc, 6)})
    component_rows = [{'component': j + 1, **{f: round(float(components[i, j]), 6) for i, f in enumerate(FEATURES)}, 'source_variance': round(float(values[order[j]]), 6)} for j in range(dim)]
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=True)
    for name, items in [('comparison.csv', comparison), ('records.csv', rows), ('source_components.csv', component_rows), ('stress_check.csv', stress)]:
        with (out / name).open('w', newline='', encoding='utf-8') as h:
            w = csv.DictWriter(h, fieldnames=list(items[0]))
            w.writeheader()
            w.writerows(items)
    (out / 'summary.json').write_text(json.dumps({'evaluation_split': split, 'source_unlabeled_count': len(source), 'target_train_count': len(train), 'borrowed_dimensions': dim, 'comparison': comparison, 'stress_check': stress, 'note': 'borrowed_frozen 是从课程提供的无标签源数据学到并冻结的 PCA 表示；这里只训练下游输出层，不是大型预训练模型，也没有微调表示。'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('S11 完成：先看 comparison.csv，再看 source_components.csv 与 stress_check.csv。')
    print(f'结果写入：{out}')
if __name__ == '__main__':
    main()
