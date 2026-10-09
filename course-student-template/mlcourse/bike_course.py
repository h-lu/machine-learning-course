"""前七课共享的真实 Bike 数据实验；科学产物确定，测试期始终封存。

只依赖 Python 标准库和 NumPy。字段说明与操作流程由各课学习页提供；
本模块生成实验记录，不代写解释、报告或所有候选方案。
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


OFFICIAL_SHA256 = "e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f"
TRAIN_END = datetime(2012, 7, 1)
VALIDATION_END = datetime(2012, 10, 1)
DATA_COLUMNS = ["instant", "dteday", "season", "yr", "mnth", "hr", "holiday",
                "weekday", "workingday", "weathersit", "temp", "atemp", "hum",
                "windspeed", "casual", "registered", "cnt"]
CALENDAR_FIELDS = {"hr", "mnth", "season", "holiday", "weekday", "workingday"}
WEATHER_FIELDS = {"temp", "atemp", "hum", "windspeed", "weathersit"}
INPUT_FIELDS = CALENDAR_FIELDS | WEATHER_FIELDS
DEFAULTS = {
    1: {"intercept": 30.0, "slope": 300.0, "inspect_count": 12},
    2: {"method": "temp_linear", "inspect_count": 12},
    3: {"purpose": "same_hour_estimation", "input_fields": ["temp", "hr", "workingday"],
        "rule_field": "temp", "intercept": 30.0, "slope": 300.0,
        "alert_threshold": 200.0, "inspect_count": 12},
    4: {},
    5: {"split": "time", "seed": 17, "method": "temp_linear", "leakage_demo": False},
    6: {"method": "hour_mean", "alert_threshold": 300.0, "daily_capacity": 4,
        "underestimate_weight": 2.0, "inspect_count": 12},
    7: {"stage": "select", "method": "coverage", "seeds": [11, 29, 47],
        "initial_size": 240, "budget": 120,
        "selection_note": "先按小时和工作日覆盖不足选择，记录随机对照。",
        "selection_plan": "artifacts/select/selection_plan.json"},
}


class CsvRows(list):
    """列表附带表头，以便没有提醒时也生成可读的空 CSV。"""
    def __init__(self, rows=(), columns=None):
        super().__init__(rows)
        self.columns = list(columns if columns is not None else (self[0].keys() if self else []))


def _json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def _safe_path(root, name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("路径应是非空字符串")
    path = (Path(root) / name).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError(f"路径须在学生仓库内：{name}")
    return path


def _lesson_path(root, lesson_dir, name):
    """兼容从课目录和学生根复制的命令；绝对路径仍限制在学生根内。"""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("路径应是非空字符串")
    value = Path(name)
    first = value.parts[0]
    root_prefixed = first.startswith("lesson-") and first[len("lesson-"):].isdigit()
    base = Path(root) if value.is_absolute() or root_prefixed else Path(lesson_dir)
    return _safe_path(root, str(base / value))


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} 须为 {low} 至 {high} 的整数")


def _number(value, name, low=None):
    if type(value) not in (int, float) or not np.isfinite(value):
        raise ValueError(f"{name} 须为有限数值")
    if low is not None and value < low:
        raise ValueError(f"{name} 须不小于 {low}")


def validate_config(lesson, supplied):
    if type(lesson) is not int or lesson not in DEFAULTS:
        raise ValueError("此程序仅用于第 01 至 07 课")
    if not isinstance(supplied, dict):
        raise ValueError("配置顶层须为 JSON 对象")
    if any(not isinstance(name, str) for name in supplied):
        raise ValueError("配置字段名须为字符串")
    allowed = set(DEFAULTS[lesson]) | {"data"}
    unknown = set(supplied) - allowed
    if unknown:
        raise ValueError(f"未知配置字段：{sorted(unknown)}；01–07 不开放测试集")
    config = {"data": "data/bike/hour.csv", **DEFAULTS[lesson], **supplied}
    if not isinstance(config["data"], str):
        raise ValueError("data 须为学生仓库内的相对路径字符串")
    for name in ("intercept", "slope"):
        if name in config:
            _number(config[name], name)
    if "inspect_count" in config:
        _integer(config["inspect_count"], "inspect_count", 1, 100)
    if lesson in (2, 5) and (not isinstance(config["method"], str) or config["method"] not in {"mean", "temp_linear"}):
        raise ValueError("method 只能选 mean 或 temp_linear")
    if lesson == 3:
        if not isinstance(config["purpose"], str) or config["purpose"] not in {"same_hour_estimation", "day_ahead_schedule"}:
            raise ValueError("purpose 只能选 same_hour_estimation 或 day_ahead_schedule")
        fields = config["input_fields"]
        if (not isinstance(fields, list) or not fields or
                any(not isinstance(field, str) for field in fields)):
            raise ValueError("input_fields 须为不为空的字段名列表")
        if len(fields) != len(set(fields)):
            raise ValueError("input_fields 不应重复")
        forbidden = set(fields) - INPUT_FIELDS
        if forbidden:
            raise ValueError(f"不可作为预测输入的字段：{sorted(forbidden)}；cnt、casual、registered 会泄漏标签")
        if config["purpose"] == "day_ahead_schedule" and set(fields) & WEATHER_FIELDS:
            raise ValueError("前一天排班时不能把未来当小时实际天气当作已知输入")
        if not isinstance(config["rule_field"], str) or config["rule_field"] not in {"temp", "hr"} or config["rule_field"] not in fields:
            raise ValueError("rule_field 只能是 input_fields 中的 temp 或 hr")
        _number(config["alert_threshold"], "alert_threshold", 0)
    if lesson == 5:
        if not isinstance(config["split"], str) or config["split"] not in {"time", "random"}:
            raise ValueError("split 只能选 time 或 random")
        _integer(config["seed"], "seed", 0, 2**32 - 1)
        if type(config["leakage_demo"]) is not bool:
            raise ValueError("leakage_demo 须为 true 或 false")
    if lesson == 6:
        if not isinstance(config["method"], str) or config["method"] not in {"temp_linear", "hour_mean"}:
            raise ValueError("method 只能选 temp_linear 或 hour_mean")
        _number(config["alert_threshold"], "alert_threshold", 0)
        _integer(config["daily_capacity"], "daily_capacity", 1, 24)
        _number(config["underestimate_weight"], "underestimate_weight", 1)
    if lesson == 7:
        if not isinstance(config["stage"], str) or config["stage"] not in {"select", "reveal"}:
            raise ValueError("stage 只能选 select 或 reveal")
        if not isinstance(config["method"], str) or config["method"] not in {"random", "coverage"}:
            raise ValueError("method 只能选 random 或 coverage")
        seeds = config["seeds"]
        if not isinstance(seeds, list) or not 2 <= len(seeds) <= 8:
            raise ValueError("seeds 须列出 2 至 8 个固定 seed，全部结果都保留")
        for seed in seeds:
            _integer(seed, "seed", 0, 2**32 - 1)
        if len(seeds) != len(set(seeds)):
            raise ValueError("seeds 不应重复")
        _integer(config["initial_size"], "initial_size", 48, 3000)
        _integer(config["budget"], "budget", 24, 1000)
        if not isinstance(config["selection_note"], str) or len(config["selection_note"].strip()) < 10:
            raise ValueError("selection_note 须在揭示前写出至少 10 字的选择理由")
        if not isinstance(config["selection_plan"], str):
            raise ValueError("selection_plan 须为课目录内的相对计划路径")
    return config


def _read_rows(path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != OFFICIAL_SHA256:
        raise ValueError("hour.csv SHA-256 与官方原件不符；请使用随包数据，不修改原始 CSV")
    rows = []
    empty_fields = 0
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != DATA_COLUMNS:
            raise ValueError("数据须含官方顺序的 17 列")
        for line, raw in enumerate(reader, 2):
            if None in raw or any(v is None or not v.strip() for v in raw.values()):
                raise ValueError(f"数据第 {line} 行存在缺列/空值，先核对原文件，不补 0")
            try:
                row = {name: int(raw[name]) for name in DATA_COLUMNS if name not in
                       {"dteday", "temp", "atemp", "hum", "windspeed"}}
                for name in ("temp", "atemp", "hum", "windspeed"):
                    row[name] = float(raw[name])
                row["datetime"] = datetime.strptime(raw["dteday"], "%Y-%m-%d") + timedelta(hours=row["hr"])
            except (ValueError, TypeError) as error:
                raise ValueError(f"数据第 {line} 行数值或日期无法读取") from error
            if not 0 <= row["hr"] <= 23:
                raise ValueError(f"数据第 {line} 行小时不在 0–23")
            if row["casual"] + row["registered"] != row["cnt"] or row["cnt"] < 0:
                raise ValueError("原文件 casual+registered=cnt 完整性核对失败")
            if not all(np.isfinite(row[name]) for name in WEATHER_FIELDS if name != "weathersit"):
                raise ValueError("原文件天气值非有限数")
            rows.append(row)
    rows.sort(key=lambda row: row["datetime"])
    times = [row["datetime"] for row in rows]
    duplicate_hours = len(times) - len(set(times))
    if not rows or duplicate_hours:
        raise ValueError("数据为空或日期小时重复，先核对文件版本")
    expected = int((times[-1] - times[0]).total_seconds() // 3600) + 1
    audit = {"rows": len(rows), "columns": len(DATA_COLUMNS), "empty_fields": empty_fields,
             "duplicate_hours": duplicate_hours, "expected_calendar_hours": expected,
             "absent_timestamp_rows": expected - len(rows),
             "first_datetime": _stamp(rows[0]), "last_datetime": _stamp(rows[-1]),
             "data_sha256": digest,
             "absent_timestamp_policy": "只记录缺行，不造需求 0，也不填补目标值",
             "target_identity_check": "casual+registered=cnt；只做原文件完整性核对，不作为输入"}
    return rows, audit


def _stamp(row):
    return row["datetime"].isoformat(timespec="minutes")


def _partition(rows):
    # 统一入口直接隔离封存记录。拟合和评价函数只接收 train/validation。
    train = [row for row in rows if row["datetime"] < TRAIN_END]
    validation = [row for row in rows if TRAIN_END <= row["datetime"] < VALIDATION_END]
    sealed_count = sum(row["datetime"] >= VALIDATION_END for row in rows)
    if not train or not validation:
        raise ValueError("固定开发切分为空，请核对原文件")
    return train, validation, sealed_count


def _fit(rows, method):
    if not rows or any(row["datetime"] >= VALIDATION_END for row in rows):
        raise ValueError("拟合样本须来自开发区间，测试期封存")
    target = np.asarray([row["cnt"] for row in rows], dtype=float)
    result = {"method": method, "training_rows": len(rows), "fallback_mean": float(np.mean(target))}
    if method == "mean":
        result["prediction"] = result["fallback_mean"]
    elif method == "temp_linear":
        x = np.asarray([row["temp"] for row in rows], dtype=float)
        centered = x - np.mean(x)
        denominator = float(np.dot(centered, centered))
        slope = float(np.dot(centered, target - np.mean(target)) / denominator) if denominator else 0.0
        result.update(intercept=float(np.mean(target) - slope * np.mean(x)), slope=slope, used_inputs=["temp"])
    elif method in {"hour_mean", "hour_workingday_mean"}:
        groups = defaultdict(list)
        for row in rows:
            key = str(row["hr"]) if method == "hour_mean" else f'{row["hr"]}:{row["workingday"]}'
            groups[key].append(row["cnt"])
        result["group_means"] = {key: float(np.mean(values)) for key, values in sorted(groups.items())}
        result["group_counts"] = {key: len(values) for key, values in sorted(groups.items())}
        result["used_inputs"] = ["hr"] if method == "hour_mean" else ["hr", "workingday"]
    else:
        raise ValueError("未知拟合方法")
    return result


def _predict(rows, model):
    method = model["method"]
    if method == "mean":
        return np.full(len(rows), model["prediction"], dtype=float)
    if method in {"manual_rule", "temp_linear"}:
        field = model.get("rule_field", "temp")
        predictions = np.maximum(0.0, np.asarray([model["intercept"] + model["slope"] * row[field]
                                                for row in rows], dtype=float))
        if not np.all(np.isfinite(predictions)):
            raise ValueError("规则参数导致数值溢出；请缩小 intercept/slope，结果不写成有效实验")
        return predictions
    result = []
    for row in rows:
        key = str(row["hr"]) if method == "hour_mean" else f'{row["hr"]}:{row["workingday"]}'
        result.append(model["group_means"].get(key, model["fallback_mean"]))
    return np.asarray(result)


def _prediction_records(rows, model, **extra):
    if any(row["datetime"] >= VALIDATION_END for row in rows):
        raise ValueError("01–07 的预测评价不读取封存测试期")
    result = CsvRows()
    for row, prediction in zip(rows, _predict(rows, model)):
        prediction = float(prediction)
        signed = prediction - row["cnt"]
        result.append({"instant": row["instant"], "datetime": _stamp(row), "partition": "validation",
                       "hr": row["hr"], "workingday": row["workingday"], "temp": row["temp"],
                       "method": model["method"], **extra, "prediction": prediction, "cnt": row["cnt"],
                       "signed_error": signed, "absolute_error": abs(signed)})
    result.columns = list(result[0])
    return result


def _metrics(records):
    if not records:
        raise ValueError("评价记录为空")
    return {"n": len(records), "mae": float(np.mean([record["absolute_error"] for record in records])),
            "mean_signed_error": float(np.mean([record["signed_error"] for record in records])),
            "underestimated_rows": sum(record["signed_error"] < 0 for record in records),
            "mae_unit": "次租赁/小时", "mae_denominator": len(records)}


def _trace(records, count):
    return CsvRows(records[:count], records.columns)


def _outcome(alert, actual):
    return "true_positive" if alert and actual else "false_positive" if alert else "false_negative" if actual else "true_negative"


def _decision_metrics(records, alert_column):
    counts = Counter(record["outcome"] for record in records)
    tp, fp, fn, tn = (counts[name] for name in ("true_positive", "false_positive", "false_negative", "true_negative"))
    return {"true_positive": tp, "false_positive": fp, "false_negative": fn, "true_negative": tn,
            "total_rows": len(records), "predicted_alert_rows": sum(bool(r[alert_column]) for r in records),
            "actual_high_rows": tp + fn, "precision": tp / (tp + fp) if tp + fp else None,
            "precision_denominator": tp + fp, "recall": tp / (tp + fn) if tp + fn else None,
            "recall_denominator": tp + fn}


def _manual(config):
    return {"method": "manual_rule", "intercept": config["intercept"], "slope": config["slope"],
            "rule_field": config.get("rule_field", "temp"), "training_rows": 0,
            "used_inputs": [config.get("rule_field", "temp")], "nonnegative_prediction": True}


def _calendar_audit(rows, audit):
    seen = {row["datetime"] for row in rows}
    month_expected, hour_expected = Counter(), Counter()
    missing = CsvRows(columns=["datetime", "month", "hr", "partition"])
    current, end = rows[0]["datetime"], rows[-1]["datetime"]
    while current <= end:
        month = current.strftime("%Y-%m")
        month_expected[month] += 1
        hour_expected[current.hour] += 1
        if current not in seen:
            missing.append({"datetime": current.isoformat(timespec="minutes"), "month": month,
                            "hr": current.hour,
                            "partition": "development" if current < VALIDATION_END else "sealed_test"})
        current += timedelta(hours=1)
    month_observed = Counter(row["datetime"].strftime("%Y-%m") for row in rows)
    hour_observed = Counter(row["hr"] for row in rows)
    month_csv = CsvRows({"month": key, "expected_hours": month_expected[key],
                        "observed_rows": month_observed[key], "missing_hours": month_expected[key] - month_observed[key]}
                       for key in sorted(month_expected))
    hour_csv = CsvRows({"hr": key, "expected_hours": hour_expected[key],
                       "observed_rows": hour_observed[key], "missing_hours": hour_expected[key] - hour_observed[key]}
                      for key in range(24))
    records = CsvRows({"instant": row["instant"], "datetime": _stamp(row),
                       "partition": "development" if row["datetime"] < VALIDATION_END else "sealed_test"}
                      for row in rows)
    return {"audit.json": audit, "coverage_month.csv": month_csv, "coverage_hour.csv": hour_csv,
            "missing_hours.csv": missing, "records.csv": records}


def _plan_settings(config):
    return {key: config[key] for key in ("method", "seeds", "initial_size", "budget", "selection_note")}


def _build_plan(train, config, digest):
    if config["initial_size"] + config["budget"] >= len(train):
        raise ValueError("initial_size + budget 须小于训练期样本数，保留未标注池")
    groups = defaultdict(list)
    by_id = {row["instant"]: row for row in train}
    for row in train:
        groups[(row["hr"], row["workingday"])].append(row["instant"])
    group_keys = sorted(groups)
    scenarios = []
    # 一个 seed 的初始集对所有候选一致。轮流遍历随机顺序的48组使初始覆盖可核对。
    for seed in config["seeds"]:
        rng = np.random.default_rng(seed)
        queues = {key: list(rng.permutation(groups[key])) for key in group_keys}
        initial = []
        while len(initial) < config["initial_size"]:
            for position in rng.permutation(len(group_keys)):
                key = group_keys[int(position)]
                if queues[key] and len(initial) < config["initial_size"]:
                    initial.append(int(queues[key].pop()))
        initial_set = set(initial)
        pool = [row["instant"] for row in train if row["instant"] not in initial_set]
        methods = ["random", "coverage"] if config["method"] == "coverage" else ["random"]
        selections = {}
        for method in methods:
            choice_rng = np.random.default_rng(np.random.SeedSequence([seed, 701]))
            if method == "random":
                selected = [int(value) for value in choice_rng.permutation(pool)[:config["budget"]]]
            else:
                counts = Counter((by_id[value]["hr"], by_id[value]["workingday"]) for value in initial)
                candidate_queues = {key: [int(value) for value in choice_rng.permutation(
                    [value for value in groups[key] if value not in initial_set])] for key in group_keys}
                selected = []
                for _ in range(config["budget"]):
                    available = [key for key in group_keys if candidate_queues[key]]
                    minimum = min(counts[key] for key in available)
                    ties = [key for key in available if counts[key] == minimum]
                    key = ties[int(choice_rng.integers(len(ties)))]
                    selected.append(candidate_queues[key].pop())
                    counts[key] += 1
            selections[method] = selected
        scenarios.append({"seed": seed, "initial_ids": initial, "pool_size": len(pool), "selections": selections})
    return {"plan_version": 1, "data_sha256": digest, "training_end_exclusive": "2012-07-01",
            "labels_revealed": False, "selection_uses": ["hr", "workingday", "seed"],
            "settings": _plan_settings(config), "scenarios": scenarios}


def _selection_manifest(plan, train):
    by_id = {row["instant"]: row for row in train}
    result = CsvRows(columns=["seed", "method", "role", "selection_order", "instant", "datetime", "hr", "workingday"])
    for scenario in plan["scenarios"]:
        for method, selected in scenario["selections"].items():
            for role, values in (("initial", scenario["initial_ids"]), ("selected", selected)):
                for position, value in enumerate(values, 1):
                    row = by_id[value]
                    result.append({"seed": scenario["seed"], "method": method, "role": role,
                                   "selection_order": position, "instant": value, "datetime": _stamp(row),
                                   "hr": row["hr"], "workingday": row["workingday"]})
    return result


def _load_plan(root, config, expected):
    # root 是学生根，计划限定于 lesson-07，不能借读取任意文件取得标签。
    path = _lesson_path(root, root / "lesson-07", config["selection_plan"])
    if not path.is_relative_to((root / "lesson-07").resolve()):
        raise ValueError("selection_plan 须在 lesson-07 内")
    try:
        supplied = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError("找不到选择计划；先 stage=select，把无标签选择和理由保存后再揭示") from error
    except json.JSONDecodeError as error:
        raise ValueError("选择计划 JSON 无法读取；保留原始 select 输出") from error
    if supplied != expected:
        raise ValueError("选择计划与配置/原数据/确定性编号不符；不得在看到标签后改计划，先核对保留的 select 输出")
    return supplied


def run_lesson(root: Path, lesson: int, config: dict) -> dict[str, object]:
    """运行一个已选择的课内实验，返回文件内容，不写磁盘。"""
    root = Path(root).resolve()
    config = validate_config(lesson, config)
    rows, audit = _read_rows(_safe_path(root, config["data"]))
    train, validation, sealed_count = _partition(rows)
    summary = {"status": "ok", "lesson": lesson, "data_sha256": audit["data_sha256"],
               "source_rows": len(rows), "training_rows": len(train), "validation_rows": len(validation),
               "sealed_test_rows": sealed_count,
               "test_policy": "01–07 仅审计封存期行数，不拟合、不评价封存期目标",
               "evaluation_partition": "validation", "train_end_exclusive": "2012-07-01",
               "validation_end_exclusive": "2012-10-01"}
    outputs = {"summary.json": summary, "config_snapshot.json": config}
    if lesson == 1:
        model = _manual(config)
        records = _prediction_records(validation, model)
        summary.update(metrics={"manual_rule": _metrics(records)}, selected_method="manual_rule")
        outputs.update({"model.json": model, "records.csv": records, "trace.csv": _trace(records, config["inspect_count"])})
    elif lesson == 2:
        selected = _fit(train, config["method"])
        records = _prediction_records(validation, selected)
        summary.update(selected_method=config["method"], metrics={config["method"]: _metrics(records)})
        all_records = CsvRows(records, records.columns)
        models = {config["method"]: selected}
        if config["method"] != "mean":
            baseline = _fit(train, "mean")
            baseline_records = _prediction_records(validation, baseline)
            models["mean"] = baseline
            summary["metrics"]["mean"] = _metrics(baseline_records)
            all_records.extend(baseline_records)
        outputs.update({"model.json": {"selected_method": config["method"], "models": models},
                        "records.csv": all_records, "trace.csv": _trace(records, config["inspect_count"])})
    elif lesson == 3:
        model = _manual(config)
        records = _prediction_records(validation, model)
        for record in records:
            record["alert"] = int(record["prediction"] >= config["alert_threshold"])
            record["actual_high"] = int(record["cnt"] >= config["alert_threshold"])
            record["outcome"] = _outcome(record["alert"], record["actual_high"])
        records.columns = list(records[0])
        field_rows = []
        for field in DATA_COLUMNS:
            allowed = field in INPUT_FIELDS and (config["purpose"] == "same_hour_estimation" or field in CALENDAR_FIELDS)
            reason = "已知日历" if field in CALENDAR_FIELDS else "实际当小时天气" if field in WEATHER_FIELDS else "目标及其组成" if field in {"cnt", "casual", "registered"} else "编号/时间索引，不作本课预测输入"
            field_rows.append({"field": field, "allowed_for_purpose": int(allowed),
                               "declared_input": int(field in config["input_fields"]),
                               "used_by_rule": int(field == config["rule_field"]), "reason": reason})
        summary.update(purpose=config["purpose"], declared_inputs=config["input_fields"],
                       used_inputs=model["used_inputs"], alert_threshold=config["alert_threshold"],
                       metrics={"manual_rule": _metrics(records)}, decision_counts=_decision_metrics(records, "alert"))
        outputs.update({"model.json": model, "records.csv": records,
                        "field_audit.csv": CsvRows(field_rows),
                        "alerts.csv": CsvRows([record for record in records if record["alert"]], records.columns),
                        "trace.csv": _trace(records, config["inspect_count"])})
    elif lesson == 4:
        summary.update(evaluation_partition="none; integrity/coverage audit only", audit=audit)
        outputs.update(_calendar_audit(rows, audit))
    elif lesson == 5:
        if config["split"] == "random":
            development = train + validation
            positions = np.random.default_rng(config["seed"]).permutation(len(development))
            val_positions = set(int(position) for position in positions[:len(validation)])
            train = [row for i, row in enumerate(development) if i not in val_positions]
            validation = [row for i, row in enumerate(development) if i in val_positions]
        model = _fit(train, config["method"])
        records = _prediction_records(validation, model)
        summary.update(split=config["split"], seed=config["seed"], training_rows=len(train), validation_rows=len(validation),
                       metrics={config["method"]: _metrics(records)}, leakage_demo_enabled=config["leakage_demo"])
        train_ids = {row["instant"] for row in train}
        manifest = CsvRows({"instant": row["instant"], "datetime": _stamp(row),
                            "partition": "train" if row["instant"] in train_ids else "validation"}
                           for row in sorted(train + validation, key=lambda row: row["datetime"]))
        outputs.update({"model.json": model, "records.csv": records, "split_manifest.csv": manifest})
        if config["leakage_demo"]:
            invalid = CsvRows({"instant": row["instant"], "datetime": _stamp(row), "valid_experiment": False,
                               "method": "INVALID_target_sum_leakage", "casual": row["casual"],
                               "registered": row["registered"], "prediction": row["casual"] + row["registered"],
                               "cnt": row["cnt"], "absolute_error": 0}
                              for row in validation)
            outputs["INVALID_leakage_records.csv"] = invalid
            outputs["INVALID_leakage_demo.json"] = {"valid_experiment": False,
                "warning": "故意错误示范：casual+registered=cnt；预测前不知道目标组成，不能用于合法比较或宣称泛化",
                "n": len(invalid), "invalid_mae": 0.0, "included_in_legal_metrics": False}
    elif lesson == 6:
        model = _fit(train, config["method"])
        records = _prediction_records(validation, model)
        daily = defaultdict(list)
        for record in records:
            record["candidate_alert"] = int(record["prediction"] >= config["alert_threshold"])
            record["final_alert"] = 0
            record["actual_high"] = int(record["cnt"] >= config["alert_threshold"])
            daily[record["datetime"][:10]].append(record)
        daily_records = []
        for date, values in sorted(daily.items()):
            candidates = [r for r in values if r["candidate_alert"]]
            selected = sorted(candidates, key=lambda r: (-r["prediction"], r["datetime"]))[:config["daily_capacity"]]
            for record in selected:
                record["final_alert"] = 1
            daily_records.append({"date": date, "observed_hours": len(values), "candidates": len(candidates),
                                  "selected": len(selected), "daily_capacity": config["daily_capacity"]})
        for record in records:
            record["outcome"] = _outcome(record["final_alert"], record["actual_high"])
            record["weighted_absolute_error"] = record["absolute_error"] * (
                config["underestimate_weight"] if record["signed_error"] < 0 else 1)
            if not np.isfinite(record["weighted_absolute_error"]):
                raise ValueError("underestimate_weight 导致加权误差溢出；请使用较小的有限权重")
        records.columns = list(records[0])
        metrics = _metrics(records)
        metrics.update(weighted_mae=float(np.mean([r["weighted_absolute_error"] for r in records])),
                       weighted_mae_denominator=len(records), underestimate_weight=config["underestimate_weight"])
        summary.update(metrics={config["method"]: metrics}, alert_threshold=config["alert_threshold"],
                       daily_capacity=config["daily_capacity"], decision_counts=_decision_metrics(records, "final_alert"),
                       capacity_protocol="同一天离线批次；按预测降序选最多 capacity 条，同分按时间先后；未利用当天真实标签分配容量")
        outputs.update({"model.json": model, "records.csv": records, "daily_capacity.csv": CsvRows(daily_records),
                        "trace.csv": _trace(records, config["inspect_count"])})
    elif lesson == 7:
        plan = _build_plan(train, config, audit["data_sha256"])
        manifest = _selection_manifest(plan, train)
        summary.update(stage=config["stage"], method=config["method"], seeds=config["seeds"],
                       initial_size=config["initial_size"], budget=config["budget"],
                       labels_revealed=config["stage"] == "reveal", seed_policy="保留全部固定 seed，不按分数挑选")
        if config["stage"] == "select":
            summary["evaluation_partition"] = "none; label-free selection only"
            outputs.update({"selection_plan.json": plan, "selection_manifest.csv": manifest, "records.csv": manifest})
        else:
            plan = _load_plan(root, config, plan)
            by_id = {row["instant"]: row for row in train}
            all_records = CsvRows()
            learning = CsvRows()
            revealed = CsvRows(columns=list(manifest.columns) + ["cnt"])
            for record in manifest:
                revealed.append({**record, "cnt": by_id[record["instant"]]["cnt"]})
            for scenario in plan["scenarios"]:
                initial = [by_id[value] for value in scenario["initial_ids"]]
                for method, selected_ids in scenario["selections"].items():
                    for budget_used, fit_rows in ((0, initial), (config["budget"], initial + [by_id[value] for value in selected_ids])):
                        model = _fit(fit_rows, "hour_workingday_mean")
                        records = _prediction_records(validation, model, seed=scenario["seed"],
                                                      selection_method=method, budget_used=budget_used)
                        metrics = _metrics(records)
                        learning.append({"seed": scenario["seed"], "selection_method": method,
                                         "budget_used": budget_used, "training_rows": len(fit_rows),
                                         "validation_rows": metrics["n"], "mae": metrics["mae"],
                                         "mae_denominator": metrics["mae_denominator"]})
                        all_records.extend(records)
            all_records.columns = list(all_records[0])
            learning.columns = list(learning[0])
            summary["results"] = list(learning)
            outputs.update({"selection_plan.json": plan, "selection_manifest.csv": manifest,
                            "revealed_training.csv": revealed, "learning_curve.csv": learning,
                            "records.csv": all_records})
    return outputs


def _write_outputs(directory, outputs, rebuild_default=False):
    directory.mkdir(parents=True, exist_ok=rebuild_default)
    for name, value in outputs.items():
        path = directory / name
        if name.endswith(".json"):
            path.write_text(_json_text(value), encoding="utf-8")
        else:
            columns = value.columns if isinstance(value, CsvRows) else list(value[0])
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
                writer.writeheader()
                writer.writerows(value)


def main(lesson_dir: Path, lesson_number: int):
    lesson_dir = Path(lesson_dir).resolve()
    root = lesson_dir.parent
    parser = argparse.ArgumentParser(description=f"第 {lesson_number:02d} 课真实 Bike 开发集实验；测试期封存")
    parser.add_argument("--config", default="config.json", help="配置路径，相对于本课目录")
    parser.add_argument("--output", help="新输出目录，相对于本课目录；已存在时拒绝覆盖")
    args = parser.parse_args()
    try:
        config_path = _lesson_path(root, lesson_dir, args.config)
        try:
            supplied = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"config 第 {error.lineno} 行 JSON 格式错误；核对引号、逗号和冒号") from error
        config = validate_config(lesson_number, supplied)
        output_name = args.output or ("artifacts/select" if lesson_number == 7 and config["stage"] == "select" else "artifacts/run")
        output = _lesson_path(root, lesson_dir, output_name)
        if args.output is not None and output.exists():
            raise ValueError(f"输出目录已存在：{output}；用 --output artifacts/新名称 保留每次比较")
        outputs = run_lesson(root, lesson_number, config)
        _write_outputs(output, outputs, rebuild_default=args.output is None)
    except (ValueError, OSError) as error:
        print(f"运行未完成：{error}", file=sys.stderr)
        raise SystemExit(2) from error
    print(f"第 {lesson_number:02d} 课运行完成：{output}")
    print("先打开 summary.json，再按本课 SUPPORT 读取具体 CSV；测试期保持封存。")
