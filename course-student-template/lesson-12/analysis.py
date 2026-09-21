"""S10：追踪逻辑回归的一次梯度更新与完整学习曲线。"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
FEATURES = ['message_length', 'history_count', 'urgency_count', 'attachment_missing']

def matrix(records, mean=None, std=None):
    raw = np.array([[r[k] for k in FEATURES] for r in records], float)
    if mean is None:
        mean = raw.mean(axis=0)
        std = raw.std(axis=0)
        std[std == 0] = 1
    scaled = (raw - mean) / std
    return (np.column_stack([np.ones(len(raw)), scaled]), np.array([r['needs_review'] for r in records], float), mean, std)

def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -30, 30)))

def loss(x, y, w):
    p = np.clip(sigmoid(x @ w), 1e-09, 1 - 1e-09)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))

def accuracy(x, y, w):
    return float(np.mean((sigmoid(x @ w) >= 0.5) == y))

def train(tx, ty, vx, vy, rate, epochs):
    w = np.zeros(tx.shape[1])
    trace = []
    first = None
    for epoch in range(epochs + 1):
        if epoch in {0, 1, 2, 5, 10, 20, 40, 80, 160, 320, epochs}:
            trace.append({'epoch': epoch, 'train_log_loss': round(loss(tx, ty, w), 8), 'evaluation_log_loss': round(loss(vx, vy, w), 8)})
        if epoch == epochs:
            break
        gradient = tx.T @ (sigmoid(tx @ w) - ty) / len(ty)
        new = w - rate * gradient
        if first is None:
            first = (w.copy(), gradient.copy(), new.copy())
        w = new
    return (w, trace, first)

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
    epochs = int(c['epochs'])
    rates = {'starting_rate': float(c['learning_rate']), 'comparison_rate': float(c['comparison_learning_rate'])}
    if epochs < 1 or any((rate <= 0 for rate in rates.values())):
        raise ValueError('训练轮数和学习率必须为正数')
    records = json.loads((HERE / 'data/base.json').read_text(encoding='utf-8'))['records']
    tr = [r for r in records if r['split'] == 'train']
    ev = [r for r in records if r['split'] == split]
    tx, ty, mean, std = matrix(tr)
    vx, vy, _, _ = matrix(ev, mean, std)
    comparison = []
    all_trace = []
    update_rows = []
    record_rows = []
    for name, rate in rates.items():
        w, trace, first = train(tx, ty, vx, vy, rate, epochs)
        comparison.append({'method': name, 'learning_rate': rate, 'epochs': epochs, 'train_log_loss': round(loss(tx, ty, w), 8), 'evaluation_log_loss': round(loss(vx, vy, w), 8), 'train_accuracy': round(accuracy(tx, ty, w), 6), 'evaluation_accuracy': round(accuracy(vx, vy, w), 6)})
        for row in trace:
            all_trace.append({'method': name, **row})
        if name == 'starting_rate':
            names = ['intercept'] + FEATURES
            for feature, before, gradient, after in zip(names, *first):
                update_rows.append({'parameter': feature, 'before': round(float(before), 8), 'gradient': round(float(gradient), 8), 'after': round(float(after), 8), 'update_direction': 'decrease' if after < before else 'increase'})
        probs = sigmoid(vx @ w)
        for source, prob in zip(ev, probs):
            record_rows.append({'id': source['id'], 'split': split, 'method': name, 'actual': source['needs_review'], 'probability': round(float(prob), 8), 'predicted': int(prob >= 0.5)})
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=True)
    for name, items in [('comparison.csv', comparison), ('learning_curve.csv', all_trace), ('first_update.csv', update_rows), ('records.csv', record_rows)]:
        with (out / name).open('w', newline='', encoding='utf-8') as h:
            w = csv.DictWriter(h, fieldnames=list(items[0]))
            w.writeheader()
            w.writerows(items)
    (out / 'summary.json').write_text(json.dumps({'evaluation_split': split, 'counts': {'train': len(tr), split: len(ev)}, 'feature_scaling': {'mean': dict(zip(FEATURES, mean.tolist())), 'std': dict(zip(FEATURES, std.tolist()))}, 'comparison': comparison, 'first_update': update_rows, 'note': '损失下降只说明当前优化目标变小；不单独证明概率可直接用于行动，也不证明新场景有效。'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('S10 完成：先看 first_update.csv 的更新方向，再看 learning_curve.csv。')
    print(f'结果写入：{out}')
if __name__ == '__main__':
    main()
