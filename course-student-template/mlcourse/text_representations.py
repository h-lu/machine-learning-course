"""Lesson11 train-only text representations and one-run comparison tools.

NumPy only. Sparse lexical rows avoid a train_rows × vocabulary dense matrix.
The original lesson10 loader, manual features, objective and action rules remain
available unchanged. This module never opens a final evaluation partition.
"""
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import time

import numpy as np

from . import sms_course as baseline


def tokenize(text, token_pattern="words_numbers"):
    if not isinstance(text, str):
        raise ValueError("Text must be a string; empty text is permitted")
    if token_pattern == "words_numbers":
        return baseline.tokens(text)
    if token_pattern == "words":
        return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())
    raise ValueError("token_pattern must be words or words_numbers")


@dataclass
class SparseRows:
    """Small CSR-like matrix supporting only the operations used in this lesson."""
    indptr: np.ndarray
    indices: np.ndarray
    data: np.ndarray
    shape: tuple

    def __post_init__(self):
        self.row_indices = np.repeat(np.arange(self.shape[0]), np.diff(self.indptr))

    def __len__(self):
        return self.shape[0]

    def row(self, index):
        start, end = self.indptr[index:index + 2]
        return self.indices[start:end], self.data[start:end]

    def matvec(self, weights):
        return np.bincount(self.row_indices, weights=self.data * np.asarray(weights)[self.indices], minlength=self.shape[0])

    def transpose_matvec(self, values):
        return np.bincount(self.indices, weights=self.data * np.asarray(values)[self.row_indices], minlength=self.shape[1])

    def to_dense(self, max_cells=1_000_000):
        if self.shape[0] * self.shape[1] > max_cells:
            raise ValueError("Dense conversion exceeds the requested cell budget")
        matrix = np.zeros(self.shape)
        matrix[self.row_indices, self.indices] = self.data
        return matrix


def fit_representation(texts, kind="bow", min_df=2, max_features=1200,
                       token_pattern="words_numbers", normalization="l2"):
    texts = list(texts)
    if not texts:
        raise ValueError("Fit needs nonempty training texts")
    if kind == "manual":
        rep = baseline.fit_representation(texts, "manual")
        rep["training_documents"] = len(texts)
        rep["normalization"] = "training mean and standard deviation per feature"
        return rep
    if kind not in {"bow", "tfidf"}:
        raise ValueError("representation must be manual, bow or tfidf")
    if type(min_df) is not int or not 1 <= min_df <= len(texts):
        raise ValueError("min_df must be an integer between 1 and training row count")
    if type(max_features) is not int or not 1 <= max_features <= 10000:
        raise ValueError("max_features must be an integer between 1 and 10000")
    if normalization not in {"l2", "none"}:
        raise ValueError("normalization must be l2 or none")
    frequencies = Counter(token for text in texts for token in set(tokenize(text, token_pattern)))
    candidates = sorted((word for word in frequencies if frequencies[word] >= min_df), key=lambda word: (-frequencies[word], word))
    names = sorted(candidates[:max_features])
    if not names:
        raise ValueError("Empty training vocabulary; inspect tokens/min_df before choosing a new setting")
    return {
        "kind": kind, "names": names, "training_documents": len(texts),
        "df": [frequencies[word] for word in names],
        "idf": [float(np.log((1 + len(texts)) / (1 + frequencies[word])) + 1) for word in names],
        "min_df": min_df, "max_features": max_features,
        "token_pattern": token_pattern, "normalization": normalization,
        "tf": "raw within-document count", "idf_formula": "log((1+N_train)/(1+df_train))+1",
        "selection": "training df descending, alphabetical tie; retained coordinates alphabetical",
        "training_texts_sha256": hashlib.sha256(json.dumps(texts, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest(),
    }


def transform(texts, rep):
    texts = list(texts)
    if rep["kind"] == "manual":
        return baseline.transform(texts, rep)
    positions = {word: i for i, word in enumerate(rep["names"])}
    indices, values, offsets = [], [], [0]
    for text in texts:
        counts = Counter(tokenize(text, rep["token_pattern"]))
        row = sorted((positions[word], count) for word, count in counts.items() if word in positions)
        row_values = np.array([count * (rep["idf"][index] if rep["kind"] == "tfidf" else 1) for index, count in row], dtype=float)
        norm = float(np.linalg.norm(row_values))
        if rep["normalization"] == "l2" and norm:
            row_values /= norm
        indices.extend(index for index, _ in row)
        values.extend(row_values)
        offsets.append(len(indices))
    return SparseRows(np.asarray(offsets, dtype=np.int64), np.asarray(indices, dtype=np.int64), np.asarray(values, dtype=float), (len(texts), len(positions)))


def explain_text(text, rep):
    if rep["kind"] == "manual":
        raw = baseline.manual([text])[0]
        value = baseline.transform([text], rep)[0]
        return {"tokens": baseline.tokens(text), "unknown_tokens": [], "row_norm": float(np.linalg.norm(value)),
                "features": [{"index": i, "name": name, "raw_value": float(raw[i]), "training_mean": rep["mean"][i], "training_scale": rep["scale"][i], "value": float(value[i])} for i, name in enumerate(rep["names"])]}
    sequence = tokenize(text, rep["token_pattern"])
    counts = Counter(sequence)
    names = {word: i for i, word in enumerate(rep["names"])}
    features = []
    for word in sorted(counts):
        if word in names:
            i = names[word]
            weighted = counts[word] * (rep["idf"][i] if rep["kind"] == "tfidf" else 1)
            features.append({"index": i, "name": word, "count": counts[word], "df": rep["df"][i], "idf": rep["idf"][i], "weighted_value": float(weighted)})
    norm = float(np.sqrt(sum(item["weighted_value"] ** 2 for item in features)))
    for item in features:
        item["value"] = item["weighted_value"] / norm if norm and rep["normalization"] == "l2" else item["weighted_value"]
    return {"tokens": sequence, "unknown_tokens": [{"token": word, "count": counts[word]} for word in sorted(counts) if word not in names], "row_norm": norm,
            "training_documents": rep["training_documents"], "normalization": rep["normalization"], "features": features}


def _matvec(matrix, values):
    return matrix.matvec(values) if isinstance(matrix, SparseRows) else matrix @ values


def loss_gradient(matrix, labels, weights, intercept, l2=0., sample_weights=None):
    if not isinstance(matrix, SparseRows):
        return baseline.loss_gradient(matrix, labels, weights, intercept, l2, sample_weights)
    labels = np.asarray(labels, dtype=float)
    a = np.ones(len(labels)) if sample_weights is None else np.asarray(sample_weights, dtype=float)
    if not len(labels) or matrix.shape[0] != len(labels) or not np.isfinite(matrix.data).all() or not np.isfinite(labels).all() or not np.isin(labels, [0, 1]).all():
        raise ValueError("Need finite nonempty binary data")
    if a.shape != labels.shape or not np.isfinite(a).all() or (a <= 0).any() or not np.isfinite(l2) or l2 < 0:
        raise ValueError("Invalid sample weights or regularization")
    logits = matrix.matvec(weights) + intercept
    error = a * (baseline.sigmoid(logits) - labels) / a.sum()
    loss = float(np.dot(a, np.logaddexp(0, logits) - labels * logits) / a.sum() + l2 * np.dot(weights, weights) / 2)
    return loss, matrix.transpose_matvec(error) + l2 * weights, float(error.sum())


def fit_classifier(x, y, dev_x, dev_y, lr=1., steps=400, l2=.001,
                   spam_weight=1., seed=0, initial_scale=0.):
    if not isinstance(x, SparseRows):
        return baseline.fit(x, y, dev_x, dev_y, lr, steps, l2, spam_weight, seed, initial_scale)
    if type(steps) is not int or steps < 1 or not np.isfinite(lr) or lr <= 0 or not np.isfinite(spam_weight) or spam_weight <= 0 or not np.isfinite(initial_scale) or initial_scale < 0:
        raise ValueError("Invalid training setting")
    rng = np.random.default_rng(seed)
    weights = rng.normal(0, initial_scale, x.shape[1])
    intercept, curve, first_update = 0., [], None
    a = np.where(y == 1, spam_weight, 1.)
    for step in range(steps + 1):
        loss, gradient, bias_gradient = loss_gradient(x, y, weights, intercept, l2, a)
        dev_logits = _matvec(dev_x, weights) + intercept
        dev_loss = float(np.mean(np.logaddexp(0, dev_logits) - dev_y * dev_logits))
        if not np.isfinite(loss) or not np.isfinite(gradient).all():
            raise ValueError("Training nonfinite; inspect feature scale or learning rate")
        curve.append(dict(step=step, train_objective=loss, dev_bce=dev_loss, intercept=intercept, weight_norm=float(np.linalg.norm(weights)), gradient_norm=float(np.linalg.norm(gradient)), train_bce=loss_gradient(x, y, weights, intercept, 0.)[0], tracked_dev_probability=float(baseline.sigmoid(dev_logits[0]))))
        if step == steps:
            break
        if step == 0:
            next_w, next_b = weights - lr * gradient, intercept - lr * bias_gradient
            first_update = dict(step=0, weights_before=weights.tolist(), bias_before=intercept, gradient_weights=gradient.tolist(), gradient_bias=bias_gradient, learning_rate=lr, weights_after=next_w.tolist(), bias_after=next_b, objective_before=loss, objective_after=loss_gradient(x, y, next_w, next_b, l2, a)[0], denominator=float(a.sum()), l2=l2, spam_weight=spam_weight, note="Full-batch objective and update match lesson10; intercept is not penalized. Dev labels are monitoring only.")
        weights -= lr * gradient
        intercept -= lr * bias_gradient
    return weights, intercept, curve, first_update


def run(config, output):
    defaults = dict(representation="manual", min_df=2, max_features=1200, token_pattern="words_numbers", normalization="l2", lr=1., steps=400, l2=.001, spam_weight=1., seed=0, initial_scale=0., threshold=.5, capacity_fraction=1., trace_id=None)
    if not isinstance(config, dict) or set(config) - set(defaults):
        raise ValueError("Unknown configuration fields")
    effective = {**defaults, **config}
    out = Path(output)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("Use a new empty output directory to preserve previous evidence")
    start = time.perf_counter()
    train, dev = baseline.load_rows("train"), baseline.load_rows("dev")
    texts = [row["text"] for row in train]
    rep = fit_representation(texts, effective["representation"], effective["min_df"], effective["max_features"], effective["token_pattern"], effective["normalization"])
    x, dx = transform(texts, rep), transform([row["text"] for row in dev], rep)
    y, dy = np.array([row["label"] == "spam" for row in train], dtype=float), np.array([row["label"] == "spam" for row in dev], dtype=float)
    w, b, curve, update = fit_classifier(x, y, dx, dy, **{key: effective[key] for key in ("lr", "steps", "l2", "spam_weight", "seed", "initial_scale")})
    probability = baseline.sigmoid(_matvec(dx, w) + b)
    action = baseline.actions(probability, [row["id"] for row in dev], effective["threshold"], effective["capacity_fraction"])
    trace_index = 0 if effective["trace_id"] is None else next((i for i, row in enumerate(dev) if row["id"] == effective["trace_id"]), None)
    if trace_index is None:
        raise ValueError("trace_id must name an actual dev record")
    row = dev[trace_index]
    explanation = explain_text(row["text"], rep)
    for item in explanation["features"]:
        item["weight"] = float(w[item["index"]])
        item["contribution"] = float(item["value"] * item["weight"])
    trace = dict(explanation, id=row["id"], text=row["text"], text_sha256=row["text_sha256"], intercept=b, logit=float(_matvec(dx, w)[trace_index] + b), probability=float(probability[trace_index]), action=int(action[trace_index]), partition="dev")
    records = [dict(id=r["id"], group_id=r["group_id"], label=r["label"], probability=float(p), action=int(a), text_sha256=r["text_sha256"]) for r, p, a in zip(dev, probability, action)]
    summary = dict(metrics=baseline.metrics(dy, probability, action), partition="dev", training_rows=len(train), dimensions=x.shape[1], config=effective, final_test_opened=False, classifier="L2-regularized logistic model; unpenalized intercept; fixed full-batch steps", train_ids_sha256=hashlib.sha256("\n".join(r["id"] for r in train).encode()).hexdigest(), dev_ids_sha256=hashlib.sha256("\n".join(r["id"] for r in dev).encode()).hexdigest(), train_data_sha256=baseline.digest(baseline.DATA / "train.csv"), dev_data_sha256=baseline.digest(baseline.DATA / "dev.csv"), data_manifest_sha256=baseline.digest(baseline.DATA / "split_manifest.csv"), code_sha256=baseline.digest(__file__), baseline_code_sha256=baseline.digest(baseline.__file__), matrix_storage="sparse lexical rows" if isinstance(x, SparseRows) else "dense six manual features", training_nonzeros=int(len(x.data)) if isinstance(x, SparseRows) else int(np.count_nonzero(x)))
    out.mkdir(parents=True, exist_ok=True)
    for name, value in (("config", effective), ("representation", rep), ("summary", summary), ("prediction_trace", trace), ("first_update", update)):
        baseline.save_json(out / (name + ".json"), value)
    baseline.write_csv(out / "records.csv", records)
    baseline.write_csv(out / "curve.csv", curve)
    np.savez(out / "model.npz", w=w, b=np.array(b))
    return dict(summary, seconds=time.perf_counter() - start)
