"""基础计算：学生可以阅读、修改或使用其他库替换。"""

from __future__ import annotations
import numpy as np


def finite(value):
    array = np.asarray(value, dtype=float)
    if not np.isfinite(array).all():
        raise ValueError("数值输入必须有限；请先处理缺失值或无穷大")
    return array


def softmax(x):
    x = finite(x)
    z = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return z / z.sum(axis=-1, keepdims=True)


def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -40, 40)))


def regression(y, prediction, under_cost=2.0):
    y, prediction = finite(y), finite(prediction)
    if y.shape != prediction.shape or not len(y):
        raise ValueError("真实结果与预测必须非空且长度一致")
    error = prediction - y
    return {
        "mae": float(np.mean(abs(error))),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "asymmetric_loss": float(
            np.mean(np.where(error < 0, -under_cost * error, error))
        ),
        "n": len(y),
    }


def classification(y, p, threshold=0.5):
    y, p = finite(y), finite(p)
    if y.shape != p.shape or not len(y) or not np.isin(y, [0, 1]).all():
        raise ValueError("二分类标签必须是0或1，且与预测一一对应")
    if np.any((p < 0) | (p > 1)):
        raise ValueError("概率必须在0到1之间")
    pred = p >= threshold
    tp, fp = int(np.sum(pred & (y == 1))), int(np.sum(pred & (y == 0)))
    fn, tn = int(np.sum(~pred & (y == 1))), int(np.sum(~pred & (y == 0)))
    return {
        "n": len(y),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "accuracy": (tp + tn) / len(y),
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "brier": float(np.mean((p - y) ** 2)),
        "log_loss": float(
            -np.mean(
                y * np.log(np.clip(p, 1e-9, 1))
                + (1 - y) * np.log(np.clip(1 - p, 1e-9, 1))
            )
        ),
    }


def fit_linear(x, y, ridge=0.0):
    x, y = finite(x), finite(y)
    design = np.column_stack([np.ones(len(x)), x])
    penalty = np.eye(design.shape[1]) * ridge
    penalty[0, 0] = 0
    return np.linalg.pinv(design.T @ design + penalty) @ design.T @ y


def predict_linear(x, weights):
    return np.column_stack([np.ones(len(x)), finite(x)]) @ weights


def logistic(x, y, steps=250, lr=0.15, l2=0.0):
    x, y = finite(x), finite(y)
    if steps < 1 or not 0 < lr <= 20 or l2 < 0:
        raise ValueError("steps必须为正；learning_rate在(0,20]内；l2不能为负")
    a = np.column_stack([np.ones(len(x)), x])
    w = np.zeros(a.shape[1])
    curve = []
    for step in range(steps):
        p = sigmoid(a @ w)
        gradient = a.T @ (p - y) / len(y)
        gradient[1:] += l2 * w[1:]
        w -= lr * gradient
        if step % max(1, steps // 20) == 0 or step == steps - 1:
            curve.append(
                {
                    "step": step + 1,
                    "loss": classification(y, sigmoid(a @ w))["log_loss"],
                }
            )
    return w, curve


def split(rows):
    train = np.array([r.get("split") == "train" for r in rows])
    test = ~train
    if train.sum() < 2 or test.sum() < 2:
        raise ValueError("数据至少需要两条split=train及两条评估数据")
    return train, test


def matrix(rows, fields):
    if not rows:
        raise ValueError("rows不能为空")
    try:
        return finite([[r[f] for f in fields] for r in rows])
    except KeyError as error:
        raise ValueError(f"数据缺少字段: {error.args[0]}") from error


def fit_tree(x, y, max_depth=3, min_leaf=5):
    if not 0 <= max_depth <= 10 or min_leaf < 1:
        raise ValueError("树深度应在0到10之间，叶节点最少样本数应为正")

    def build(indices, depth):
        values = y[indices]
        leaf = {"value": float(values.mean()), "n": len(indices)}
        if depth == max_depth or len(indices) < 2 * min_leaf or np.var(values) < 1e-12:
            return leaf
        best = None
        for feature in range(x.shape[1]):
            thresholds = np.unique(
                np.quantile(x[indices, feature], np.linspace(0.1, 0.9, 9))
            )
            for threshold in thresholds:
                left = indices[x[indices, feature] <= threshold]
                right = indices[x[indices, feature] > threshold]
                if min(len(left), len(right)) < min_leaf:
                    continue
                loss = np.sum((y[left] - y[left].mean()) ** 2) + np.sum(
                    (y[right] - y[right].mean()) ** 2
                )
                if best is None or loss < best[0]:
                    best = (loss, feature, float(threshold), left, right)
        if best is None:
            return leaf
        _, feature, threshold, left, right = best
        return {
            **leaf,
            "feature": feature,
            "threshold": threshold,
            "left": build(left, depth + 1),
            "right": build(right, depth + 1),
        }

    return build(np.arange(len(y)), 0)


def predict_tree(x, tree):
    def one(row, node):
        while "feature" in node:
            node = (
                node["left"]
                if row[node["feature"]] <= node["threshold"]
                else node["right"]
            )
        return node["value"]

    return np.array([one(row, tree) for row in x])


def mlp(x, y, x_eval, hidden=10, steps=180, lr=0.12, l2=0.0, seed=1, y_eval=None):
    if not 1 <= hidden <= 128 or not 1 <= steps <= 3000 or not 0 < lr <= 20 or l2 < 0:
        raise ValueError("网络参数超出教学运行限制")
    rng = np.random.default_rng(seed)
    w1 = rng.normal(0, 0.5, (x.shape[1], hidden))
    b1 = np.zeros(hidden)
    w2 = rng.normal(0, 0.5, hidden)
    b2 = 0.0
    curve = []
    for step in range(steps):
        h = np.tanh(x @ w1 + b1)
        p = sigmoid(h @ w2 + b2)
        e = (p - y) / len(y)
        dh = np.outer(e, w2) * (1 - h * h)
        gw1 = x.T @ dh + l2 * w1
        gw2 = h.T @ e + l2 * w2
        w1 -= lr * gw1
        b1 -= lr * dh.sum(axis=0)
        w2 -= lr * gw2
        b2 -= lr * e.sum()
        if step % max(1, steps // 20) == 0 or step == steps - 1:
            record = {
                "step": step + 1,
                "train_log_loss": classification(
                    y, sigmoid(np.tanh(x @ w1 + b1) @ w2 + b2)
                )["log_loss"],
            }
            if y_eval is not None:
                record["validation_log_loss"] = classification(
                    y_eval, sigmoid(np.tanh(x_eval @ w1 + b1) @ w2 + b2)
                )["log_loss"]
            curve.append(record)

    def predict(v):
        return sigmoid(np.tanh(v @ w1 + b1) @ w2 + b2)

    return predict(x_eval), curve, predict


def kmeans(x, k=3, steps=30, seed=1):
    if not 1 <= k <= len(x):
        raise ValueError("k必须介于1和样本数量之间")
    rng = np.random.default_rng(seed)
    centres = x[rng.choice(len(x), k, replace=False)].copy()
    for _ in range(steps):
        labels = np.argmin(
            ((x[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2), axis=1
        )
        new = np.array(
            [
                x[labels == j].mean(axis=0) if (labels == j).any() else centres[j]
                for j in range(k)
            ]
        )
        if np.allclose(new, centres):
            break
        centres = new
    labels = np.argmin(((x[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2), axis=1)
    return labels, centres, float(np.sum((x - centres[labels]) ** 2))
