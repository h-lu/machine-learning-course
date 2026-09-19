"""C01–C02：用小数据解释样本、预测、基线和回归评价。仅依赖标准库。"""
from __future__ import annotations

import math
from statistics import mean

TITLES = {"C01": "怎样把一个想法变成可运行的作品", "C02": "一个结果能说明方案有用吗"}


def example_data(lesson: str) -> dict:
    """人工构造的取餐等候数据，不是真实食堂调查，也不使用随机采样。"""
    if lesson not in TITLES:
        raise ValueError("入门实验只支持 C01 和 C02")
    rows = [
        dict(id=f"train-{i+1:02d}", queue_length=i % 4, wait_minutes=y,
             period="午间" if i < 4 else "晚间", split="train")
        for i, y in enumerate([2, 2, 4, 8, 0, 4, 6, 6])
    ]
    if lesson == "C02":
        for split, samples in [
            ("validation", [(0, 1, "午间"), (1, 3, "午间"), (2, 5, "午间"), (3, 4, "晚间")]),
            ("test", [(0, 1, "午间"), (1, 3, "午间"), (2, 5, "午间"), (3, 7, "午间"),
                      (2, 4, "晚间"), (3, 4, "晚间")]),
        ]:
            rows.extend(dict(id=f"{split}-{i+1:02d}", queue_length=x, wait_minutes=y,
                             period=p, split=split) for i, (x, y, p) in enumerate(samples))
    return {"kind": "intro_waiting_time", "source": "人工构造的教学数据；单位为分钟；不代表真实食堂或学生。",
            "rows": rows}


def example_config(lesson: str) -> dict:
    return {"seed": 7, "rule_intercept": 1.0, "rule_slope": 2.0, "stress_queue": 10,
            "evaluation_split": "train" if lesson == "C01" else "validation"}


def number(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} 必须是有限数值，不能是空值、文字或无穷大")
    if value < 0:
        raise ValueError(f"{name} 不能为负数")
    return float(value)


def queue(value) -> float:
    value = number(value, "queue_length（排队人数）")
    if not value.is_integer():
        raise ValueError("queue_length（排队人数）必须是整数")
    return value


def validate(data: dict, config: dict) -> list[dict]:
    if data.get("kind") != "intro_waiting_time":
        raise ValueError("请使用本课 data/base.json 的取餐等候数据，或同时修改程序")
    rows = data.get("rows")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 10000:
        raise ValueError("rows 必须包含 1 至 10000 条样本")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("每条样本必须是包含字段的对象")
        for name in ("id", "queue_length", "wait_minutes", "period", "split"):
            if name not in row:
                raise ValueError(f"样本缺少字段：{name}")
        if not isinstance(row["id"], str) or not row["id"].strip() or row["id"] in seen:
            raise ValueError("样本 id 必须是非空且不重复的文字")
        seen.add(row["id"])
        queue(row["queue_length"])
        number(row["wait_minutes"], "wait_minutes（实际等待分钟数）")
        if not isinstance(row["period"], str) or not row["period"].strip():
            raise ValueError("period（时段）必须是非空文字")
        if not isinstance(row["split"], str) or row["split"] not in {"train", "validation", "test"}:
            raise ValueError("split 只能为 train、validation 或 test")
    for key in ("rule_intercept", "rule_slope", "stress_queue", "evaluation_split"):
        if key not in config:
            raise ValueError(f"配置缺少字段：{key}")
    number(config["rule_intercept"], "rule_intercept（规则的固定等待分钟数）")
    number(config["rule_slope"], "rule_slope（规则中每人增加的分钟数）")
    queue(config["stress_queue"])
    return rows


def fit_line(rows: list[dict]) -> tuple[float, float]:
    """一元线性回归的最小二乘解：只传入训练集。"""
    if len(rows) < 2:
        raise ValueError("线性回归至少需要两条训练样本")
    xs = [r["queue_length"] for r in rows]
    ys = [r["wait_minutes"] for r in rows]
    xbar, ybar = mean(xs), mean(ys)
    denominator = sum((x - xbar) ** 2 for x in xs)
    if denominator == 0:
        raise ValueError("训练集的排队人数全相同，无法估计斜率；请补充不同人数的样本")
    slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denominator
    return ybar - slope * xbar, slope


def predict(coefficients: tuple[float, float], value) -> float:
    x = queue(value)
    result = coefficients[0] + coefficients[1] * x
    if not math.isfinite(result):
        raise ValueError("预测值不是有限数值，请缩小数据或参数")
    return result  # 不静默截断负预测：使用条件由学生检查，而非隐藏错误。


def metrics(actual: list[float], predicted: list[float]) -> dict:
    if not actual or len(actual) != len(predicted):
        raise ValueError("真实值和预测值必须非空且一一对应")
    errors = [p - y for y, p in zip(actual, predicted)]
    return {"n": len(actual), "mae": mean(abs(e) for e in errors),
            "rmse": math.sqrt(mean(e * e for e in errors)),
            "asymmetric_loss": mean(-2 * e if e < 0 else e for e in errors)}


def experiment(lesson: str, data: dict, config: dict) -> dict:
    rows = validate(data, config)
    train = [r for r in rows if r["split"] == "train"]
    if not train:
        raise ValueError("缺少训练集：至少保留一条 split=train 的样本")
    evaluation_split = config["evaluation_split"]
    allowed = {"train"} if lesson == "C01" else {"validation", "test"}
    if not isinstance(evaluation_split, str) or evaluation_split not in allowed:
        raise ValueError("C01 只核对训练样本；C02 只在 validation 或 test 上评价")
    evaluation = [r for r in rows if r["split"] == evaluation_split]
    if not evaluation:
        raise ValueError(f"没有 split={evaluation_split} 的样本，不能计算该数据集的误差")
    rule = (float(config["rule_intercept"]), float(config["rule_slope"]))
    models = {"rule": rule}
    if lesson == "C02":
        models.update(baseline=(mean(r["wait_minutes"] for r in train), 0.0), linear=fit_line(train))
    primary = "rule" if lesson == "C01" else "linear"
    actual = [r["wait_minutes"] for r in evaluation]
    predictions = {name: [predict(w, r["queue_length"]) for r in evaluation] for name, w in models.items()}
    reports = {name: metrics(actual, ps) for name, ps in predictions.items()}
    by_period = {}
    records = []
    for index, row in enumerate(evaluation):
        record = {"id": row["id"], "period": row["period"], "queue_length": row["queue_length"],
                  "actual": row["wait_minutes"]}
        for name, ps in predictions.items():
            record[f"prediction_{name}"] = ps[index]
            record[f"absolute_error_{name}"] = abs(ps[index] - row["wait_minutes"])
        records.append(record)
    for period in sorted({r["period"] for r in evaluation}):
        indices = [i for i, r in enumerate(evaluation) if r["period"] == period]
        by_period[period] = {name: metrics([actual[i] for i in indices], [ps[i] for i in indices])
                             for name, ps in predictions.items()}
    stress_queue = config["stress_queue"]
    lo, hi = min(r["queue_length"] for r in train), max(r["queue_length"] for r in train)
    stress = {"queue_length": stress_queue, "outside_training_range": not lo <= stress_queue <= hi,
              "predictions": {name: predict(w, stress_queue) for name, w in models.items()},
              "actual": None, "mae": None}
    return {"metrics": {**reports[primary], "row_count": len(rows)},
            "comparison": {name: report for name, report in reports.items() if name != primary},
            "stress_test": {"change": "输入一个新的排队人数；没有实际等待时间，只检查预测，不能计算误差", "metrics": stress},
            "details": {"evaluation_split": evaluation_split, "primary_model": primary,
                        "train_ids": [r["id"] for r in train], "evaluation_ids": [r["id"] for r in evaluation],
                        "actual": actual, "prediction": predictions[primary], "predictions": records,
                        "coefficients": list(models[primary]), "model_coefficients": models,
                        "by_period": by_period,
                        "training_note": "rule 为人工设定规则；baseline 的均值和 linear 的系数仅使用训练集"}}


def c01(data: dict, config: dict) -> dict:
    return experiment("C01", data, config)


def c02(data: dict, config: dict) -> dict:
    return experiment("C02", data, config)
