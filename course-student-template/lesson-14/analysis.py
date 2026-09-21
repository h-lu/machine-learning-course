"""S12：用控制变量实验区分训练不足、过拟合与表示不合适。"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
BASE = ['message_length', 'history_count', 'urgency_count', 'attachment_missing']

def raw(records):
    return np.array([[r[k] for k in BASE] for r in records], float)

def build(records, mean, std, expanded):
    x = (raw(records) - mean) / std
    if expanded:
        return np.column_stack([x, x * x, x[:, 0] * x[:, 2], x[:, 1] * x[:, 3]])
    return x

def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -30, 30)))

def logloss(x, y, w):
    p = np.clip(sigmoid(x @ w), 1e-09, 1 - 1e-09)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))

def train(tx, y, vx, vy, epochs, reg, rate=0.12):
    tx = np.column_stack([np.ones(len(tx)), tx])
    vx = np.column_stack([np.ones(len(vx)), vx])
    w = np.zeros(tx.shape[1])
    trace = []
    for e in range(epochs + 1):
        if e in {0, 10, 20, 40, 80, 160, 320, epochs}:
            trace.append({'epoch': e, 'train_log_loss': round(logloss(tx, y, w), 8), 'evaluation_log_loss': round(logloss(vx, vy, w), 8)})
        if e == epochs:
            break
        g = tx.T @ (sigmoid(tx @ w) - y) / len(y)
        g[1:] += reg * w[1:]
        w -= rate * g
    return (w, trace, tx, vx)

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
    change = c['diagnostic_change']
    valid = {'more_epochs', 'stronger_regularization', 'simpler_representation'}
    if change not in valid:
        raise ValueError(f'diagnostic_change 只能是 {sorted(valid)}')
    records = json.loads((HERE / 'data/base.json').read_text(encoding='utf-8'))['records']
    tr = [r for r in records if r['split'] == 'train']
    ev = [r for r in records if r['split'] == split]
    mean = raw(tr).mean(0)
    std = raw(tr).std(0)
    std[std == 0] = 1
    y = np.array([r['needs_review'] for r in tr], float)
    ey = np.array([r['needs_review'] for r in ev], float)
    settings = {'starting': {'expanded': True, 'epochs': 80, 'regularization': 0.0}}
    settings['candidate'] = {'expanded': True, 'epochs': 320 if change == 'more_epochs' else 80, 'regularization': 0.2 if change == 'stronger_regularization' else 0.0}
    if change == 'simpler_representation':
        settings['candidate']['expanded'] = False
    comparison = []
    curves = []
    rows = []
    for name, s in settings.items():
        tx = build(tr, mean, std, s['expanded'])
        vx = build(ev, mean, std, s['expanded'])
        w, trace, txb, vxb = train(tx, y, vx, ey, s['epochs'], s['regularization'])
        tp = sigmoid(txb @ w)
        vp = sigmoid(vxb @ w)
        comparison.append({'method': name, 'changed_factor': change if name == 'candidate' else 'none', 'feature_count': tx.shape[1], 'epochs': s['epochs'], 'regularization': s['regularization'], 'train_log_loss': round(logloss(txb, y, w), 8), 'evaluation_log_loss': round(logloss(vxb, ey, w), 8), 'train_accuracy': round(float(np.mean((tp >= 0.5) == y)), 6), 'evaluation_accuracy': round(float(np.mean((vp >= 0.5) == ey)), 6)})
        for row in trace:
            curves.append({'method': name, **row})
        for r, prob in zip(ev, vp):
            rows.append({'id': r['id'], 'split': split, 'method': name, 'actual': r['needs_review'], 'probability': round(float(prob), 8), 'predicted': int(prob >= 0.5)})
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=True)
    for name, items in [('comparison.csv', comparison), ('learning_curve.csv', curves), ('records.csv', rows)]:
        with (out / name).open('w', newline='', encoding='utf-8') as h:
            w = csv.DictWriter(h, fieldnames=list(items[0]))
            w.writeheader()
            w.writerows(items)
    (out / 'summary.json').write_text(json.dumps({'evaluation_split': split, 'diagnostic_change': change, 'comparison': comparison, 'note': '一次实验只能直接检验它改变的因素；小验证集上的差异还可能受样本波动影响。'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('S12 完成：先比较 comparison.csv 的训练与评价损失，再看 learning_curve.csv。')
    print(f'结果写入：{out}')
if __name__ == '__main__':
    main()
