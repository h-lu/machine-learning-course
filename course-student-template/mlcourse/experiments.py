"""32个可改写的小实验。默认选择仅供理解计算，不是课程标准答案。"""

from __future__ import annotations
import numpy as np
from .mathops import (
    finite,
    softmax,
    sigmoid,
    regression,
    classification,
    fit_linear,
    predict_linear,
    logistic,
    split,
    matrix,
    fit_tree,
    predict_tree,
    mlp,
    kmeans,
)


def outcome(metrics, comparison, change, stress, details=None):
    return {
        "metrics": metrics,
        "comparison": comparison,
        "stress_test": {"change": change, "metrics": stress},
        "details": details or {},
    }


def table(d):
    rows = d["rows"]
    x = matrix(rows, ["x1", "x2"])
    y = matrix(rows, ["target"]).ravel()
    label = matrix(rows, ["label"]).ravel()
    tr, te = split(rows)
    return rows, x, y, label, tr, te


def prediction_details(y, p):
    return {"actual": np.asarray(y).tolist(), "prediction": np.asarray(p).tolist()}


# C01–C02 使用新的连续回归案例；S01–S30 的实现保持不变。
from .intro import c01, c02














def s07(d, c):
    _, x, y, _, tr, te = table(d)
    if c["ridge"] < 0:
        raise ValueError("ridge不能为负")
    w = fit_linear(x[tr], y[tr], c["ridge"])
    p = predict_linear(x[te], w)
    far = x[te].copy()
    far[:, 0] += c["extrapolation_distance"]
    # Explicitly constructed changed relationship; not claimed to be observed truth.
    far_truth = (
        2 + 1.5 * far[:, 0] - 0.7 * far[:, 1] + 0.5 * np.maximum(far[:, 0] - 2, 0) ** 2
    )
    return outcome(
        regression(y[te], p),
        {"training_mean": regression(y[te], np.full(te.sum(), y[tr].mean()))},
        "在x1增大的区间加入已声明的非线性真实关系",
        regression(far_truth, predict_linear(far, w)),
        {
            **prediction_details(y[te], p),
            "coefficients": w.tolist(),
            "extrapolation_x": far.tolist(),
            "extrapolation_actual": far_truth.tolist(),
        },
    )


def s08(d, c):
    _, x, _, y, tr, te = table(d)
    w, curve = logistic(x[tr], y[tr], c["steps"], c["learning_rate"], c["l2"])
    p = sigmoid(predict_linear(x[te], w))
    return outcome(
        classification(y[te], p, c["threshold"]),
        {
            "constant_probability": classification(
                y[te], np.full(te.sum(), y[tr].mean())
            )
        },
        "评估特征整体增加2",
        classification(y[te], sigmoid(predict_linear(x[te] + 2, w)), c["threshold"]),
        {
            **prediction_details(y[te], p),
            "coefficients": w.tolist(),
            "train_curve": curve,
        },
    )


def s09(d, c):
    _, x, _, y, tr, te = table(d)
    tree = fit_tree(x[tr], y[tr], c["max_depth"], c["min_leaf"])
    p = predict_tree(x[te], tree)
    deep = fit_tree(x[tr], y[tr], min(10, c["max_depth"] + 3), 1)
    return outcome(
        classification(y[te], p),
        {
            "training": classification(y[tr], predict_tree(x[tr], tree)),
            "deeper_evaluation": classification(y[te], predict_tree(x[te], deep)),
        },
        "给评估输入增加0.3的测量偏差",
        classification(y[te], predict_tree(x[te] + 0.3, tree)),
        {**prediction_details(y[te], p), "tree": tree},
    )


def s10(d, c):
    _, x, _, y, tr, te = table(d)
    xt, yt = x[tr], y[tr]
    n = int(c["n_estimators"])
    if not 1 <= n <= 50 or not 0 < c["learning_rate"] <= 1:
        raise ValueError("n_estimators应在1到50之间，learning_rate应在(0,1]")
    rng = np.random.default_rng(c["seed"])
    trees = []
    for _ in range(n):
        sample = rng.integers(0, len(yt), len(yt))
        trees.append(fit_tree(xt[sample], yt[sample], c["max_depth"]))

    def bag(v):
        return np.mean([predict_tree(v, t) for t in trees], axis=0)

    train_prediction = np.full(len(yt), yt.mean())
    boost = []
    for _ in range(n):
        tree = fit_tree(xt, yt - train_prediction, c["max_depth"])
        boost.append(tree)
        train_prediction += c["learning_rate"] * predict_tree(xt, tree)

    def boosted(v):
        return np.clip(
            yt.mean()
            + c["learning_rate"] * np.sum([predict_tree(v, t) for t in boost], axis=0),
            0,
            1,
        )

    one = fit_tree(xt, yt, c["max_depth"])
    p = bag(x[te])
    return outcome(
        classification(y[te], p),
        {
            "single_tree": classification(y[te], predict_tree(x[te], one)),
            "boosting": classification(y[te], boosted(x[te])),
        },
        "给评估特征增加0.8的偏差",
        {
            "bagging": classification(y[te], bag(x[te] + 0.8)),
            "boosting": classification(y[te], boosted(x[te] + 0.8)),
        },
        {
            **prediction_details(y[te], p),
            "model_tree_counts": {"single": 1, "bagging": n, "boosting": n},
            "operations_proxy": {
                "single": len(y[te]) * c["max_depth"],
                "bagging": len(y[te]) * c["max_depth"] * n,
            },
        },
    )


def s11(d, c):
    _, x, _, _, _, _ = table(d)
    mean = x.mean(axis=0)
    scale = np.maximum(x.std(axis=0), 1e-8)
    z = (x - mean) / scale if c["standardize"] else x
    labels, centres, inertia = kmeans(z, c["k"], seed=c["seed"])
    altered = x.copy()
    altered[:, 1] *= c["scale_multiplier"]
    other = altered
    if c["standardize"]:
        other = (altered - altered.mean(axis=0)) / np.maximum(altered.std(axis=0), 1e-8)
    changed, _, new_inertia = kmeans(other, c["k"], seed=c["seed"])
    pair_agreement = float(
        np.mean((labels[:, None] == labels) == (changed[:, None] == changed))
    )
    raw_labels, _, raw_inertia = kmeans(x, c["k"], seed=c["seed"])
    return outcome(
        {
            "inertia": inertia,
            "cluster_sizes": np.bincount(labels, minlength=c["k"]).tolist(),
        },
        {
            "without_scaling": {
                "inertia": raw_inertia,
                "cluster_sizes": np.bincount(raw_labels, minlength=c["k"]).tolist(),
            }
        },
        "改变第二列的计量单位，再按选定流程重跑",
        {"pair_agreement": pair_agreement, "inertia": new_inertia},
        {
            "assignments": labels.tolist(),
            "centres": centres.tolist(),
            "note": "inertia依赖尺度，不能直接跨单位比较；分组只描述相似性",
        },
    )


def s12(d, c):
    _, x, _, _, tr, te = table(d)
    k = int(c["components"])
    capacity = int(c["review_capacity"])
    if not 1 <= k <= x.shape[1] or not 1 <= capacity <= int(te.sum()):
        raise ValueError("components或review_capacity超出数据形状")
    mean = x[tr].mean(axis=0)
    _, s, vt = np.linalg.svd(x[tr] - mean, full_matrices=False)
    basis = vt[:k]

    def errors(v):
        centred = v - mean
        return np.mean((centred - centred @ basis.T @ basis) ** 2, axis=1)

    score = errors(x[te])
    perturbed = x[te].copy()
    perturbed[0] += np.array([8, -8])
    new = errors(perturbed)
    return outcome(
        {
            "mean_reconstruction_error": float(score.mean()),
            "explained_variance_ratio": float(np.sum(s[:k] ** 2) / np.sum(s**2)),
        },
        {"review_indices": np.argsort(-score)[:capacity].tolist()},
        "给第一条评估数据加入异常偏移",
        {
            "first_error_before": float(score[0]),
            "first_error_after": float(new[0]),
            "first_is_in_review": bool(0 in np.argsort(-new)[:capacity]),
        },
        {
            "reconstruction_errors": score.tolist(),
            "basis": basis.tolist(),
            "mean": mean.tolist(),
            "note": "异常分数不能自动说明记录是错误的",
        },
    )


def s13(d, c):
    _, x, _, y, tr, te = table(d)
    p, curve, predict = mlp(
        x[tr],
        y[tr],
        x[te],
        c["hidden"],
        c["steps"],
        c["learning_rate"],
        c["l2"],
        c["seed"],
        y_eval=y[te],
    )
    w, _ = logistic(x[tr], y[tr])
    linear = sigmoid(predict_linear(x[te], w))
    return outcome(
        classification(y[te], p),
        {"logistic": classification(y[te], linear)},
        "输入全部加1，但结果标签不变，模拟测量基准变化",
        classification(y[te], predict(x[te] + 1)),
        {
            **prediction_details(y[te], p),
            "train_curve": curve,
            "parameter_count": 2 * c["hidden"] + 2 * c["hidden"] + 1,
        },
    )


def s14(d, c):
    _, x, _, y, tr, te = table(d)
    p, curve, predict = mlp(
        x[tr],
        y[tr],
        x[te],
        c["hidden"],
        c["steps"],
        c["learning_rate"],
        c["l2"],
        c["seed"],
        y_eval=y[te],
    )
    q, other, _ = mlp(
        x[tr],
        y[tr],
        x[te],
        c["hidden"],
        c["steps"],
        c["comparison_learning_rate"],
        c["l2"],
        c["seed"],
        y_eval=y[te],
    )
    rng = np.random.default_rng(c["seed"])
    noisy = x[te] + rng.normal(0, 0.5, x[te].shape)
    return outcome(
        classification(y[te], p),
        {"other_learning_rate": classification(y[te], q)},
        "评估特征加入标准差0.5的噪声",
        classification(y[te], predict(noisy)),
        {
            **prediction_details(y[te], p),
            "train_curve": curve,
            "comparison_curve": other,
        },
    )


def convolution_features(images):
    # Two 3x3 filters: vertical and horizontal contrast, followed by ReLU/max pooling.
    kernels = np.array(
        [
            [[-1, 2, -1], [-1, 2, -1], [-1, 2, -1]],
            [[-1, -1, -1], [2, 2, 2], [-1, -1, -1]],
        ],
        dtype=float,
    )
    patches = np.lib.stride_tricks.sliding_window_view(images, (3, 3), axis=(1, 2))
    maps = np.einsum("nhwij,kij->nkhw", patches, kernels)
    return np.maximum(maps, 0).max(axis=(2, 3)), maps


def s15(d, c):
    rows = d["rows"]
    images = finite([r["pixels"] for r in rows])
    y = matrix(rows, ["label"]).ravel()
    tr, te = split(rows)
    if images.ndim != 3 or min(images.shape[1:]) < 3:
        raise ValueError("图像必须为相同大小、至少3×3的灰度数组")
    features, maps = convolution_features(images)
    scale = np.maximum(features[tr].std(axis=0), 1e-8)
    mean = features[tr].mean(axis=0)
    z = (features - mean) / scale
    w, curve = logistic(z[tr], y[tr], c["steps"], c["learning_rate"])
    p = sigmoid(predict_linear(z[te], w))
    flat = images.reshape(len(images), -1)
    pixel, _, pixel_predict = mlp(
        flat[tr],
        y[tr],
        flat[te],
        hidden=8,
        steps=c["steps"],
        lr=c["learning_rate"],
        seed=c["seed"],
    )
    shifted = np.roll(images[te], int(c["shift_pixels"]), axis=2)
    shift_features, _ = convolution_features(shifted)
    q = sigmoid(predict_linear((shift_features - mean) / scale, w))
    return outcome(
        classification(y[te], p),
        {"pixel_mlp": classification(y[te], pixel)},
        "沿水平方向循环平移图像；卷积核固定，分类头已训练",
        {
            "convolution_head": classification(y[te], q),
            "pixel_mlp": classification(
                y[te], pixel_predict(shifted.reshape(len(shifted), -1))
            ),
        },
        {
            **prediction_details(y[te], p),
            "train_curve": curve,
            "first_feature_maps": maps[0].tolist(),
            "pooled_features": features.tolist(),
            "trainable_component": "仅分类头；卷积核为人工方向滤波器",
        },
    )


def s16(d, c):
    rows = d["rows"]
    raw = finite([r["raw"] for r in rows])
    embedding = finite([r["embedding"] for r in rows])
    y = matrix(rows, ["label"]).ravel()
    tr, te = split(rows)
    n = int(c["training_examples"])
    indices = np.flatnonzero(tr)
    if not 2 <= n <= len(indices):
        raise ValueError("training_examples必须介于2与训练记录总数之间")
    selected = np.random.default_rng(c["seed"]).permutation(indices)[:n]
    if c["representation"] not in {"matched", "mismatched"}:
        raise ValueError("representation应为matched或mismatched")
    matched = embedding if c["representation"] == "matched" else embedding[:, [1]]

    def predict(x):
        return np.clip(
            predict_linear(x[te], fit_linear(x[selected], y[selected], c["ridge"])),
            0,
            1,
        )

    p = predict(matched)
    negative = predict(embedding[:, [1]])
    return outcome(
        classification(y[te], p),
        {"raw_features": classification(y[te], predict(raw))},
        "只保留与标签关系不匹配的表示方向",
        classification(y[te], negative),
        {
            **prediction_details(y[te], p),
            "training_ids": [rows[i]["id"] for i in selected],
            "representation_source": d["representation_source"],
            "no_finetuning_performed": True,
        },
    )


def attention(vectors, causal=True, temperature=1.0):
    x = finite(vectors)
    if x.ndim != 2 or not len(x) or temperature <= 0:
        raise ValueError("attention需要非空二维向量及正温度")
    width = x.shape[1]
    q = x
    k = x
    v = x
    scores = q @ k.T / np.sqrt(width) / temperature
    if causal:
        scores = np.where(np.triu(np.ones_like(scores, dtype=bool), 1), -1e9, scores)
    weights = softmax(scores)
    return weights, weights @ v


def s17(d, c):
    x = finite(d["vectors"])
    weights, out = attention(x, c["causal"], c["temperature"])
    unmasked, other = attention(x, False, c["temperature"])
    a, b = c["swap_positions"]
    if not 0 <= a < len(x) or not 0 <= b < len(x):
        raise ValueError("swap_positions超出词元位置")
    reordered = x.copy()
    reordered[[a, b]] = reordered[[b, a]]
    changed, output = attention(reordered, c["causal"], c["temperature"])
    aligned_output = output.copy()
    aligned_output[[a, b]] = aligned_output[[b, a]]
    return outcome(
        {
            "row_sum_max_error": float(abs(weights.sum(axis=1) - 1).max()),
            "future_attention_mass": float(np.triu(weights, 1).sum()),
            "output_norm": float(np.linalg.norm(out)),
        },
        {
            "unmasked_future_mass": float(np.triu(unmasked, 1).sum()),
            "unmasked_output_norm": float(np.linalg.norm(other)),
        },
        "交换两个位置的词元向量，再运行相同遮罩",
        {
            "output_change_l2": float(np.linalg.norm(out - output)),
            "aligned_output_change_l2": float(np.linalg.norm(out - aligned_output)),
        },
        {
            "tokens": d["tokens"],
            "attention_weights": weights.tolist(),
            "output_vectors": out.tolist(),
            "changed_weights": changed.tolist(),
            "projection": "Q、K、V均采用输入本身，等价于固定单位投影；不是已训练注意力",
            "order_note": "本课没有位置编码；无遮罩时换序使输出行随之重排。先按原词元顺序对齐，再判断输出是否改变，不能把行重排说成理解了顺序。",
        },
    )


def transformer(vectors, causal, seed):
    x = finite(vectors)
    rng = np.random.default_rng(seed)
    width = x.shape[1]
    position = np.sin(
        np.arange(len(x))[:, None] / np.power(10000, np.arange(width)[None, :] / width)
    )
    h = x + 0.1 * position
    weights, context = attention(h, causal)

    def normalize(v):
        return (v - v.mean(axis=1, keepdims=True)) / np.sqrt(
            v.var(axis=1, keepdims=True) + 1e-5
        )

    h = normalize(h + context)
    w1 = rng.normal(0, 0.3, (width, width * 2))
    w2 = rng.normal(0, 0.3, (width * 2, width))
    h = normalize(h + np.maximum(h @ w1, 0) @ w2)
    return h, weights


def s18(d, c):
    x = finite(d["vectors"])
    targets = np.asarray(d["next_token_targets"], dtype=int)
    vocab = len(d["tokens"])
    if targets.shape != (len(x),) or np.any((targets < 0) | (targets >= vocab)):
        raise ValueError("next_token_targets必须与输入等长且编号有效")
    if not 0 < c["learning_rate"] <= 1:
        raise ValueError("learning_rate应在(0,1]")
    hidden, weights = transformer(x, c["causal"], c["seed"])
    rng = np.random.default_rng(c["seed"])
    head = rng.normal(0, 0.1, (x.shape[1], vocab))
    p = softmax(hidden @ head)
    onehot = np.eye(vocab)[targets]
    before = float(-np.log(p[np.arange(len(x)), targets]).mean())
    head_after = head - c["learning_rate"] * hidden.T @ (p - onehot) / len(x)
    after = softmax(hidden @ head_after)
    modified = x.copy()
    modified[-1] += np.resize(np.array([3.0, -2.0, 1.0, -1.0]), x.shape[1])
    changed, _ = transformer(modified, c["causal"], c["seed"])
    return outcome(
        {
            "next_token_loss_before": before,
            "next_token_loss_after": float(
                -np.log(after[np.arange(len(x)), targets]).mean()
            ),
            "trainable_head_parameters": int(head.size),
        },
        {"uniform_next_token_loss": float(np.log(vocab))},
        "只修改最后一个词元，检查第一位置是否读取未来内容",
        {"first_position_change_l2": float(np.linalg.norm(changed[0] - hidden[0]))},
        {
            "hidden_vectors": hidden.tolist(),
            "attention_weights": weights.tolist(),
            "probabilities_before": p.tolist(),
            "probabilities_after": after.tolist(),
            "targets": targets.tolist(),
            "training_scope": "固定Transformer块，只更新一次输出头；不能支持模型学会语言的结论",
        },
    )


def tokenize(text, vocabulary):
    ordered = sorted(
        [(word, i) for i, word in enumerate(vocabulary) if not word.startswith("<")],
        key=lambda item: -len(item[0]),
    )
    ids = []
    pieces = []
    position = 0
    while position < len(text):
        found = next(
            ((word, i) for word, i in ordered if text.startswith(word, position)), None
        )
        if found:
            word, index = found
        else:
            word, index = text[position], 0
        ids.append(index)
        pieces.append(word)
        position += len(word)
    return ids, pieces


def language(d):
    vocabulary = d["vocabulary"]
    logits = finite(d["logits"])
    if (
        logits.shape != (len(vocabulary), len(vocabulary))
        or len(vocabulary) < 3
        or vocabulary[:2] != ["<unk>", "<eos>"]
    ):
        raise ValueError(
            "词表至少含3项，前两项必须是<unk>/<eos>；logits必须为词表长度乘词表长度的有限矩阵"
        )
    return vocabulary, logits


def s19(d, c):
    vocabulary, logits = language(d)
    ids, pieces = tokenize(c["text"], vocabulary)
    context = int(c["context_length"])
    if context < 1 or not ids:
        raise ValueError("text不能为空，context_length必须为正")
    kept = ids[-context:]
    pairs = list(zip(kept[:-1], kept[1:]))
    probs = softmax(logits)
    loss = (
        float(np.mean([-np.log(max(1e-12, probs[a, b])) for a, b in pairs]))
        if pairs
        else None
    )
    unknown, _ = tokenize(c["text"] + "🧭", vocabulary)
    return outcome(
        {
            "tokens": len(ids),
            "unknown_tokens": ids.count(0),
            "used_context_tokens": len(kept),
            "next_token_log_loss": loss,
            "perplexity": float(np.exp(loss)) if loss is not None else None,
        },
        {"character_count": len(c["text"]), "uniform_perplexity": len(vocabulary)},
        "给文本添加词表外符号",
        {"unknown_tokens": unknown.count(0), "tokens": len(unknown)},
        {
            "pieces": pieces,
            "token_ids": ids,
            "kept_token_ids": kept,
            "next_probabilities": probs[kept[-1]].tolist(),
            "logits_source": d["logits_source"],
        },
    )


def sampling_distribution(logits, temperature, top_k, top_p):
    if temperature <= 0 or not 1 <= top_k <= len(logits) or not 0 < top_p <= 1:
        raise ValueError("温度必须为正，top_k不能超出词表，top_p应在(0,1]")
    p = softmax(logits / temperature)
    order = np.argsort(-p, kind="stable")[:top_k]
    cumulative = np.cumsum(p[order] / p[order].sum())
    keep = order[(cumulative - p[order] / p[order].sum()) < top_p]
    filtered = np.zeros_like(p)
    filtered[keep] = p[keep]
    return filtered / filtered.sum()


def s20(d, c):
    vocabulary, logits = language(d)
    samples = int(c["samples"])
    max_tokens = int(c["max_tokens"])
    if not 1 <= samples <= 500 or not 1 <= max_tokens <= 100:
        raise ValueError("samples应在1到500，max_tokens应在1到100")

    def generate(temperature):
        rng = np.random.default_rng(c["seed"])
        sequences = []
        for _ in range(samples):
            seq = [2]
            for _ in range(max_tokens):
                p = sampling_distribution(
                    logits[seq[-1]], temperature, int(c["top_k"]), float(c["top_p"])
                )
                nxt = int(rng.choice(len(p), p=p))
                seq.append(nxt)
                if nxt == 1:
                    break
            sequences.append(seq)
        return sequences

    def report(sequences):
        return {
            "samples": len(sequences),
            "unique_sequences": len({tuple(s) for s in sequences}),
            "mean_generated_length": float(np.mean([len(s) - 1 for s in sequences])),
            "end_token_rate": float(np.mean([s[-1] == 1 for s in sequences])),
            "adjacent_repeat_rate": float(
                np.mean([np.mean(np.diff(s) == 0) for s in sequences])
            ),
        }

    seq = generate(c["temperature"])
    hot = generate(c["temperature"] * 2)
    greedy = [2]
    for _ in range(max_tokens):
        greedy.append(int(np.argmax(logits[greedy[-1]])))
        if greedy[-1] == 1:
            break
    return outcome(
        report(seq),
        {"greedy_ids": greedy, "greedy_text": "".join(vocabulary[i] for i in greedy)},
        "把温度提高一倍，使用相同种子重新抽样",
        report(hot),
        {
            "sample_ids": seq,
            "sample_text": ["".join(vocabulary[i] for i in s) for s in seq[:10]],
            "distribution_after_start": sampling_distribution(
                logits[2], c["temperature"], c["top_k"], c["top_p"]
            ).tolist(),
            "logits_source": d["logits_source"],
        },
    )


def s21(d, c):
    rows = d["rows"]
    candidate = c["candidate"]
    candidates = list(d["candidate_prompts"])
    allowed = {"room", "loan", "account", "food", "unknown"}
    if candidate not in candidates:
        raise ValueError("候选没有对应响应；先补充真实输出再评价新提示")

    def report(subset, name):
        if not subset:
            raise ValueError("development和evaluation都需要数据")
        responses = [r["responses"][name] for r in subset]
        correct = sum(a == r["expected"] for a, r in zip(responses, subset))
        invalid = sum(a not in allowed for a in responses)
        return {
            "n": len(subset),
            "correct": correct,
            "accuracy": correct / len(subset),
            "invalid_outputs": invalid,
            "weighted_error": (len(subset) - correct + c["invalid_cost"] * invalid)
            / len(subset),
        }

    evaluation = [r for r in rows if r["split"] == "evaluation"]
    development = [r for r in rows if r["split"] == "development"]
    hard = [r for r in rows if r["expected"] == "unknown"]
    return outcome(
        report(evaluation, candidate),
        {"development": {name: report(development, name) for name in candidates}},
        "单独检查应该回答unknown的已有样例",
        report(hard, candidate),
        {
            "candidate": candidate,
            "evaluation_cases": [
                {
                    "id": r["id"],
                    "expected": r["expected"],
                    "response": r["responses"][candidate],
                }
                for r in evaluation
            ],
            "source": d["response_source"],
            "unseen_prompt_evaluated": False,
        },
    )


def retrieve(d, query, top_k, active_only):
    docs = [r for r in d["documents"] if r.get("active", False) or not active_only]
    if not docs:
        return []
    q = finite(query["vector"])
    vectors = finite([r["vector"] for r in docs])
    if vectors.shape[1] != len(q) or np.linalg.norm(q) == 0:
        raise ValueError("查询和文档向量必须同维且查询不能为零")
    scores = (
        vectors
        @ q
        / np.maximum(np.linalg.norm(vectors, axis=1) * np.linalg.norm(q), 1e-12)
    )
    order = sorted(range(len(docs)), key=lambda i: (-scores[i], docs[i]["id"]))[:top_k]
    return [{"document": docs[i], "similarity": float(scores[i])} for i in order]


def retrieval_report(d, k, active):
    results = []
    for query in d["queries"]:
        items = retrieve(d, query, k, active)
        ids = [item["document"]["id"] for item in items]
        relevant = set(query["relevant"])
        hits = len(relevant & set(ids))
        results.append(
            {
                "id": query["id"],
                "retrieved": ids,
                "recall": hits / len(relevant) if relevant else None,
                "precision": hits / len(ids) if ids else 0.0,
                "scores": [r["similarity"] for r in items],
            }
        )
    recalls = [r["recall"] for r in results if r["recall"] is not None]
    return {
        "query_count": len(results),
        "mean_recall_answerable": float(np.mean(recalls)) if recalls else None,
        "mean_precision": float(np.mean([r["precision"] for r in results])),
    }, results


def s22(d, c):
    k = int(c["top_k"])
    if not 1 <= k <= len(d["documents"]):
        raise ValueError("top_k必须介于1和文档数之间")
    m, results = retrieval_report(d, k, c["active_only"])
    one, _ = retrieval_report(d, 1, c["active_only"])
    stale, stale_results = retrieval_report(d, k, False)
    return outcome(
        m,
        {"top_one": one},
        "允许检索过期文档，检查前列结果是否混入旧版本",
        stale,
        {
            "queries": results,
            "queries_with_old_versions": stale_results,
            "vector_source": d["vector_source"],
        },
    )


def rag_report(d, c):
    cases = []
    for q in d["queries"]:
        results = retrieve(d, q, c["top_k"], c["active_only"])
        chosen = (
            results[0]
            if results and results[0]["similarity"] >= c["minimum_similarity"]
            else None
        )
        citation = chosen["document"]["id"] if chosen else None
        answer = chosen["document"]["text"] if chosen else None
        correct = (citation in q["relevant"]) if q["answerable"] else chosen is None
        cases.append(
            {
                "id": q["id"],
                "answer": answer,
                "citation": citation,
                "correct": correct,
                "answerable": q["answerable"],
                "active_citation": chosen["document"]["active"] if chosen else None,
            }
        )
    unanswerable = [r for r in cases if not r["answerable"]]
    return {
        "n": len(cases),
        "correct": sum(r["correct"] for r in cases),
        "accuracy": float(np.mean([r["correct"] for r in cases])),
        "abstentions": sum(r["answer"] is None for r in cases),
        "unsupported_answers": sum(
            r["answer"] is not None and not r["correct"] for r in cases
        ),
        "unanswerable_rejection_rate": (
            float(np.mean([r["answer"] is None for r in unanswerable]))
            if unanswerable
            else None
        ),
    }, cases


def s23(d, c):
    if not 0 <= c["minimum_similarity"] <= 1 or not 1 <= c["top_k"] <= len(
        d["documents"]
    ):
        raise ValueError("minimum_similarity或top_k无效")
    m, cases = rag_report(d, c)
    permissive, other = rag_report(d, {**c, "minimum_similarity": 0.0})
    stale = {**d, "documents": [r for r in d["documents"] if r["id"] != "loan-current"]}
    stress, stress_cases = rag_report(stale, {**c, "active_only": False})
    return outcome(
        m,
        {"no_abstention_threshold": permissive},
        "撤下当前借书规则，并允许搜索旧版本",
        stress,
        {
            "cases": cases,
            "changed_cases": stress_cases,
            "generation": "直接抽取检索到的全文并给出文档id；没有调用生成式模型",
        },
    )


def request_policy(row, candidate, max_chars):
    if candidate == "allowlist":
        return row["requested_action"] in {"read_public"}
    if candidate == "keyword":
        return not any(
            word in row["request"][:max_chars] for word in ("密码", "忽略", "个人信息")
        )
    raise ValueError("candidate应为allowlist或keyword；其他机制可通过改写程序加入")


def s24(d, c):
    rows = d["rows"]
    if c["max_request_chars"] < 1:
        raise ValueError("max_request_chars必须为正")

    def report(records, candidate):
        accepted = [
            request_policy(r, candidate, c["max_request_chars"]) for r in records
        ]
        return {
            "n": len(records),
            "unsafe_actions_allowed": sum(
                a and not r["allowed"] for a, r in zip(accepted, records)
            ),
            "safe_requests_blocked": sum(
                not a and r["allowed"] for a, r in zip(accepted, records)
            ),
            "correct": sum(a == r["allowed"] for a, r in zip(accepted, records)),
        }, accepted

    m, accepted = report(rows, c["candidate"])
    other, _ = report(rows, "keyword" if c["candidate"] == "allowlist" else "allowlist")
    changed = [
        {
            **r,
            "request": "这是一个普通请求："
            + r["request"].replace("密码", "口令").replace("个人信息", "资料"),
        }
        for r in rows
    ]
    stress, _ = report(changed, c["candidate"])
    return outcome(
        m,
        {"alternative_policy": other},
        "改写危险请求表述，保留它真正申请的动作",
        stress,
        {
            "decisions": [
                {
                    "id": r["id"],
                    "requested_action": r["requested_action"],
                    "accepted": a,
                    "expected_allowed": r["allowed"],
                }
                for r, a in zip(rows, accepted)
            ],
            "limitation": "动作标签在教学数据中已知；真实工具层必须实施权限检查，不能相信模型输出的安全自述",
        },
    )


def s25(d, c):
    p = finite(d["reward_probabilities"])
    changed = finite(d["changed_probabilities"])
    if (
        len(p) != len(changed)
        or np.any((p < 0) | (p > 1))
        or np.any((changed < 0) | (changed > 1))
    ):
        raise ValueError("两组回报概率应同维且在0到1之间")
    steps = int(c["steps"])
    runs = int(c["runs"])
    epsilon = c["epsilon"]
    if not 1 <= steps <= 10000 or not 1 <= runs <= 100 or not 0 <= epsilon <= 1:
        raise ValueError("steps/runs/epsilon超出教学运行限制")

    def simulate(strategy, shift):
        totals = []
        regrets = []
        counts_all = []
        for run in range(runs):
            rng = np.random.default_rng(c["seed"] + run)
            counts = np.zeros(len(p))
            values = np.zeros(len(p))
            total = regret = 0.0
            for t in range(steps):
                current = changed if shift and t >= steps // 2 else p
                if strategy == "ucb":
                    action = int(
                        np.argmax(values + np.sqrt(2 * np.log(t + 2) / (counts + 1e-9)))
                    )
                elif rng.random() < (epsilon if strategy == "epsilon" else 0):
                    action = int(rng.integers(len(p)))
                else:
                    action = int(np.argmax(values))
                reward = float(rng.random() < current[action])
                counts[action] += 1
                values[action] += (reward - values[action]) / counts[action]
                total += reward
                regret += current.max() - current[action]
            totals.append(total)
            regrets.append(regret)
            counts_all.append(counts)
        return {
            "mean_reward": float(np.mean(totals)),
            "reward_std": float(np.std(totals)),
            "mean_pseudo_regret": float(np.mean(regrets)),
            "mean_action_counts": np.mean(counts_all, axis=0).tolist(),
            "runs": runs,
            "steps": steps,
        }

    m = simulate("epsilon", False)
    return outcome(
        m,
        {"greedy": simulate("greedy", False), "ucb": simulate("ucb", False)},
        "中途更换每个动作的回报概率",
        simulate("epsilon", True),
        {
            "regret_definition": "使用已知合成环境概率计算的期望机会损失，不等于一次实现回报之差"
        },
    )


def transition(d, state, action, bonus=0.0):
    terminal = {d["goal"], *d["hazards"]}
    if state in terminal:
        return state, 0.0, True
    width, height = d["width"], d["height"]
    row, column = divmod(state, width)
    dr, dc = [(-1, 0), (0, 1), (1, 0), (0, -1)][action]
    nr, nc = row + dr, column + dc
    nxt = nr * width + nc if 0 <= nr < height and 0 <= nc < width else state
    reward = (
        d["goal_reward"]
        if nxt == d["goal"]
        else d["hazard_reward"] if nxt in d["hazards"] else d["step_reward"]
    )
    if nxt == d["bonus_state"]:
        reward += bonus
    return nxt, float(reward), nxt in terminal


def validate_grid(d, gamma):
    if not 0 <= gamma < 1:
        raise ValueError("gamma应在[0,1)，确保本实验折扣回报收敛")
    n = d["width"] * d["height"]
    if (
        not isinstance(d["width"], int)
        or not isinstance(d["height"], int)
        or d["width"] <= 0
        or d["height"] <= 0
    ):
        raise ValueError("网格宽高必须为正整数")
    if not 4 <= n <= 100 or any(
        not 0 <= s < n for s in [d["start"], d["goal"], *d["hazards"], d["bonus_state"]]
    ):
        raise ValueError("网格状态无效或超过100状态")
    return n


def rollout(d, policy, gamma, bonus=0.0, max_steps=60, initial_state=None):
    state = d["start"] if initial_state is None else initial_state
    trajectory = []
    total = 0.0
    for step in range(max_steps):
        action = int(policy[state])
        nxt, reward, done = transition(d, state, action, bonus)
        trajectory.append(
            {"state": state, "action": action, "next_state": nxt, "reward": reward}
        )
        total += gamma**step * reward
        state = nxt
        if done:
            break
    return {
        "discounted_return": total,
        "goal_reached": state == d["goal"],
        "hazard_reached": state in d["hazards"],
        "steps": len(trajectory),
        "truncated": not (state == d["goal"] or state in d["hazards"]),
    }, trajectory


def s26(d, c):
    n = validate_grid(d, c["gamma"])
    width = d["width"]
    if c["policy"] not in {"right_then_down", "down_then_right"}:
        raise ValueError("policy应为right_then_down或down_then_right")
    right = np.array([1 if s % width < width - 1 else 2 for s in range(n)])
    down = np.array([2 if s // width < d["height"] - 1 else 1 for s in range(n)])
    policy = right if c["policy"] == "right_then_down" else down
    m, trajectory = rollout(d, policy, c["gamma"])
    other, _ = rollout(
        d, down if c["policy"] == "right_then_down" else right, c["gamma"]
    )
    a = transition(d, 0, 1)
    b = transition(d, width, 1)
    return outcome(
        m,
        {"other_route": other},
        "把状态仅记成列号：同列两个状态执行右移动作",
        {
            "observation_before": 0,
            "next_state_from_top": a[0],
            "reward_from_top": a[1],
            "next_state_from_second_row": b[0],
            "reward_from_second_row": b[1],
            "same_observation_different_reward": a[1] != b[1],
        },
        {
            "trajectory": trajectory,
            "policy": policy.tolist(),
            "state_definition": "行号和列号；观测只留列号会遗漏危险位置",
        },
    )


def value_iteration(d, gamma, tolerance=1e-8, bonus=0.0):
    n = validate_grid(d, gamma)
    if not 1e-12 <= tolerance <= 0.1:
        raise ValueError("tolerance应介于1e-12和0.1")
    values = np.zeros(n)
    q = np.zeros((n, 4))
    for iteration in range(10000):
        for state in range(n):
            for action in range(4):
                nxt, r, done = transition(d, state, action, bonus)
                q[state, action] = r + (0 if done else gamma * values[nxt])
        updated = q.max(axis=1)
        delta = float(np.max(abs(updated - values)))
        values = updated
        if delta < tolerance:
            break
    else:
        raise ValueError("价值迭代达到10000轮仍未收敛；请检查折扣、奖励或容差")
    for state in range(n):
        for action in range(4):
            nxt, r, done = transition(d, state, action, bonus)
            q[state, action] = r + (0 if done else gamma * values[nxt])
    return (
        values,
        np.argmax(q, axis=1),
        float(np.max(abs(q.max(axis=1) - values))),
        iteration + 1,
    )


def s27(d, c):
    values, policy, residual, iterations = value_iteration(
        d, c["gamma"], c["tolerance"]
    )
    m, traj = rollout(d, policy, c["gamma"])
    m.update(
        {
            "bellman_residual": residual,
            "iterations": iterations,
            "start_value": float(values[d["start"]]),
        }
    )
    _, short, _, _ = value_iteration(d, 0.2, c["tolerance"])
    short_report, _ = rollout(d, short, 0.2)
    changed = {**d, "step_reward": 0.15}
    _, new_policy, new_residual, _ = value_iteration(
        changed, c["gamma"], c["tolerance"]
    )
    stress, _ = rollout(changed, new_policy, c["gamma"])
    return outcome(
        m,
        {"gamma_0_2": short_report},
        "每走一步给正奖励，观察策略是否绕圈",
        stress,
        {
            "values": values.tolist(),
            "policy": policy.tolist(),
            "trajectory": traj,
            "changed_policy": new_policy.tolist(),
            "changed_bellman_residual": new_residual,
        },
    )


def qlearn(d, c, seed, bonus):
    n = validate_grid(d, c["gamma"])
    rng = np.random.default_rng(seed)
    q = np.zeros((n, 4))
    episodes = c["episodes"]
    if (
        not 1 <= episodes <= 3000
        or not 0 < c["alpha"] <= 1
        or not 0 <= c["epsilon"] <= 1
    ):
        raise ValueError("episodes/alpha/epsilon超出教学运行限制")
    rewards = []
    for episode in range(episodes):
        state = d["start"]
        total = 0.0
        for step in range(60):
            action = (
                int(rng.integers(4))
                if rng.random() < c["epsilon"]
                else int(np.argmax(q[state]))
            )
            nxt, r, done = transition(d, state, action, bonus)
            target = r + (0 if done else c["gamma"] * q[nxt].max())
            q[state, action] += c["alpha"] * (target - q[state, action])
            state = nxt
            total += r
            if done:
                break
        if episode % max(1, episodes // 20) == 0 or episode == episodes - 1:
            rewards.append({"episode": episode + 1, "reward": total})
    return q, np.argmax(q, axis=1), rewards


def s28(d, c):
    n = validate_grid(d, c["gamma"])
    base = []
    changed = []
    representative = None
    training_seeds = [c["seed"] + i for i in range(5)]
    evaluation_seeds = [c["seed"] + 1000 + i for i in range(5)]
    legal_starts = [
        state
        for state in range(n)
        if state not in {d["start"], d["goal"], *d["hazards"]}
    ]
    starts = [
        int(np.random.default_rng(seed).choice(legal_starts))
        for seed in evaluation_seeds
    ]
    for offset, training_seed in enumerate(training_seeds):
        q, policy, curve = qlearn(d, c, training_seed, 0.0)
        _, new_policy, _ = qlearn(d, c, training_seed, c["bonus_reward"])
        for evaluation_seed, initial_state in zip(evaluation_seeds, starts):
            report, _ = rollout(d, policy, c["gamma"], initial_state=initial_state)
            report.update(
                {
                    "training_seed": training_seed,
                    "evaluation_seed": evaluation_seed,
                    "initial_state": initial_state,
                }
            )
            base.append(report)
            new, _ = rollout(
                d,
                new_policy,
                c["gamma"],
                c["bonus_reward"],
                initial_state=initial_state,
            )
            new.update(
                {
                    "training_seed": training_seed,
                    "evaluation_seed": evaluation_seed,
                    "initial_state": initial_state,
                }
            )
            changed.append(new)
        if offset == 0:
            _, traj = rollout(d, policy, c["gamma"])
            representative = {
                "q_values": q.tolist(),
                "policy": policy.tolist(),
                "train_curve": curve,
                "trajectory_from_training_start": traj,
                "changed_policy": new_policy.tolist(),
            }

    def aggregate(reports):
        return {
            "evaluation_runs": len(reports),
            "goal_rate": float(np.mean([r["goal_reached"] for r in reports])),
            "mean_return": float(np.mean([r["discounted_return"] for r in reports])),
            "truncation_rate": float(np.mean([r["truncated"] for r in reports])),
        }

    _, optimal, _, _ = value_iteration(d, c["gamma"])
    optimal_reports = [
        rollout(d, optimal, c["gamma"], initial_state=start)[0] for start in starts
    ]
    return outcome(
        aggregate(base),
        {"known_environment_optimal_same_starts": aggregate(optimal_reports)},
        "到奖励点就给额外奖励，重新训练五个种子，并用相同的独立评估起点比较",
        aggregate(changed),
        {
            **representative,
            "per_evaluation": base,
            "changed_per_evaluation": changed,
            "training_seeds": training_seeds,
            "evaluation_seeds": evaluation_seeds,
            "evaluation_starts": starts,
            "evaluation_change": "训练从固定起点开始；评估随机选择其他合法起点，保持策略不再更新；未测试全新地图",
        },
    )


def s29(d, c):
    rows, x, y, _, tr, te = table(d)
    w = fit_linear(x[tr], y[tr])
    p = predict_linear(x[te], w)
    baseline = regression(y[te], p)
    shift = x[te] + 1.8
    new_y = y[te] + 0.2
    changed = regression(new_y, predict_linear(shift, w))
    drift = np.mean(
        abs(shift.mean(axis=0) - x[tr].mean(axis=0))
        / np.maximum(x[tr].std(axis=0), 1e-8)
    )
    changed["mean_standardized_shift"] = float(drift)
    changed["exceeds_mae_setting"] = changed["mae"] > c["max_mae"]
    changed["exceeds_drift_setting"] = drift > c["drift_threshold"]
    broken = dict(rows[0])
    broken.pop("x2")
    rejected = False
    try:
        matrix([broken], ["x1", "x2"])
    except ValueError:
        rejected = True
    return outcome(
        baseline,
        {"input_check": {"missing_x2_rejected": rejected}},
        "新批次特征增加1.8而结果只增加0.2，检查误差和分布",
        changed,
        {
            **prediction_details(y[te], p),
            "coefficients": w.tolist(),
            "latency_note": "操作数与维度可检查；本示例未模拟网络服务时延",
            "adoption_decision": None,
        },
    )


def s30(d, c):
    _, x, y, _, tr, te = table(d)
    fraction = c["training_fraction"]
    if not 0.2 <= fraction <= 1 or c["ridge"] < 0 or c["underestimate_cost"] <= 0:
        raise ValueError("training_fraction/ridge/underestimate_cost无效")
    selected = np.random.default_rng(c["seed"]).permutation(np.flatnonzero(tr))[
        : max(2, int(tr.sum() * fraction))
    ]
    w = fit_linear(x[selected], y[selected], c["ridge"])
    p = predict_linear(x[te], w)
    cost = c["underestimate_cost"]
    new_x = x[te].copy()
    new_x[:, 0] += 1.5
    new_y = y[te] + 2.5 - 0.5 * new_x[:, 1]
    old_prediction = predict_linear(new_x, w)
    half = len(new_y) // 2
    adapted = fit_linear(new_x[:half], new_y[:half], c["ridge"])
    adapted_prediction = predict_linear(new_x[half:], adapted)
    return outcome(
        regression(y[te], p, cost),
        {
            "training_mean": regression(
                y[te], np.full(te.sum(), y[selected].mean()), cost
            ),
            "adapted_on_first_half_of_new_batch": regression(
                new_y[half:], adapted_prediction, cost
            ),
            "old_on_adaptation_holdout": regression(
                new_y[half:], old_prediction[half:], cost
            ),
        },
        "在新使用场景中改变特征及结果关系，沿用原模型",
        regression(new_y, old_prediction, cost),
        {
            **prediction_details(y[te], p),
            "source_training_rows": len(selected),
            "adaptation_training_rows": half,
            "adaptation_evaluation_rows": len(new_y) - half,
            "transfer_actual": new_y.tolist(),
            "transfer_prediction": old_prediction.tolist(),
            "adoption_decision": None,
        },
    )


from .foundations import s01, s02, s03, s04, s05, s06

EXPERIMENTS = {
    "C01": c01,
    "C02": c02,
    **{f"S{i:02d}": globals()[f"s{i:02d}"] for i in range(1, 31)},
}
# Public student layout uses lesson-01..lesson-32; retain legacy keys for compatibility.
EXPERIMENTS.update({
    f"lesson-{i:02d}": EXPERIMENTS[("C" if i <= 2 else "S") + (f"{i:02d}" if i <= 2 else f"{i-2:02d}")]
    for i in range(1, 33)
})
