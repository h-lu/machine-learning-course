"""第 8 课：用训练数据拟合，按事前计划比较，选定方案后作最后评价。

仅使用随包 UCI hour.csv；读取全文件审计不等于计算测试分数。
使用 NumPy 普通最小二乘（OLS），负预测对所有方案统一截为 0。
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import platform

import numpy as np

OFFICIAL_SHA256 = "e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f"
COMMUTE_HOURS = [7, 8, 9, 16, 17, 18, 19]
SOURCE_FILES = ("scripts/lesson08.py", "scripts/bike_runtime.py", "lesson-08/analysis.py")
DEFAULTS = {
    "data": "data/bike/hour.csv", "change": "hour_onehot", "ridge_alpha": 0.0,
    "train_end": "2012-07-01", "validation_end": "2012-10-01",
    "tail_quantile": 0.9, "condition_hour_shift": 1, "error_case_count": 12,
}
REQUIRED_COLUMNS = {"instant", "dteday", "season", "yr", "mnth", "hr", "holiday",
                    "weekday", "workingday", "weathersit", "temp", "atemp", "hum",
                    "windspeed", "casual", "registered", "cnt"}
RECORD_COLUMNS = ["datetime", "split", "cnt", "hr", "workingday", "mnth", "season",
                  "weathersit", "is_commute", "is_high_demand", "method", "prediction",
                  "err_signed", "err_absolute"]
PREREG_FIELDS = {"schema_version", "change", "config_sha256", "primary_metric", "hypothesis",
                "explanation", "check_rule", "check_reason"}
DECISION_FIELDS = {"selected_method", "reason", "reviewed_validation_run", "validation_manifest_sha256"}
VALIDATION_ARTIFACTS = {"metrics.json", "summary.json", "comparison.csv", "config-used.json", "preregister-used.json",
                        "data_audit.json", "models.json", "condition_check.json", "records.csv", "group_metrics.csv",
                        "error_cases.csv", "feature_trace.csv", "source_manifest.json"}


def safe_path(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"路径必须位于当前独立学生目录：{name}")
    return path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path.name} 第 {error.lineno} 行 JSON 格式错误") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} 顶层应为 JSON 对象")
    return value


def config_from(path: Path) -> dict:
    given = read_json(path)
    unknown = set(given) - set(DEFAULTS)
    if unknown:
        raise ValueError(f"未知配置字段：{sorted(unknown)}")
    config = {**DEFAULTS, **given}
    if config["change"] not in {"hour_onehot", "workingday_interaction"}:
        raise ValueError("change 只能为 hour_onehot 或 workingday_interaction；一次只改变一个因素")
    if config["train_end"] != "2012-07-01" or config["validation_end"] != "2012-10-01":
        raise ValueError("本课固定日期切分为 2012-07-01 与 2012-10-01")
    for name in ("ridge_alpha", "tail_quantile"):
        if type(config[name]) not in (int, float) or not np.isfinite(config[name]):
            raise ValueError(f"{name} 应为有限数值")
    if config["ridge_alpha"] != 0:
        raise ValueError("本课使用普通最小二乘，ridge_alpha 必须为 0；不在本课加入正则化因素")
    if not 0 < config["tail_quantile"] < 1:
        raise ValueError("tail_quantile 应在 0 和 1 之间")
    if type(config["condition_hour_shift"]) is not int or not -12 <= config["condition_hour_shift"] <= 12:
        raise ValueError("condition_hour_shift 应为 -12 至 12 的整数")
    if type(config["error_case_count"]) is not int or not 1 <= config["error_case_count"] <= 100:
        raise ValueError("error_case_count 应为 1 至 100 的整数")
    if not isinstance(config["data"], str):
        raise ValueError("data 应为数据文件路径")
    return config


def load_data(path: Path, allow_fixture: bool = False) -> tuple[list[dict], dict]:
    data_hash = sha256(path)
    if not allow_fixture and data_hash != OFFICIAL_SHA256:
        raise ValueError("hour.csv 的 SHA-256 与已核定官方原件不一致；请使用随包原件，不修改 CSV")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if set(reader.fieldnames or []) != REQUIRED_COLUMNS:
            raise ValueError("hour.csv 应含官方 17 列，表头不一致")
        rows = []
        for number, raw in enumerate(reader, start=2):
            if any(value is None or not value.strip() for value in raw.values()):
                raise ValueError(f"第 {number} 行含空字段；不把空值填成 0")
            try:
                row = {name: int(raw[name]) for name in ("instant", "season", "yr", "mnth", "hr",
                       "holiday", "weekday", "workingday", "weathersit", "casual", "registered", "cnt")}
                row["datetime"] = datetime.strptime(raw["dteday"], "%Y-%m-%d") + timedelta(hours=row["hr"])
                for name in ("temp", "atemp", "hum", "windspeed"):
                    row[name] = float(raw[name])
            except (ValueError, TypeError) as error:
                raise ValueError(f"第 {number} 行含无法读取的日期或数值") from error
            domains = {"hr": range(24), "mnth": range(1, 13), "weekday": range(7),
                       "season": range(1, 5), "weathersit": range(1, 5),
                       "yr": range(2), "holiday": range(2), "workingday": range(2)}
            if any(row[k] not in values for k, values in domains.items()):
                raise ValueError(f"第 {number} 行类别代码不在官方字典中")
            if min(row["cnt"], row["casual"], row["registered"]) < 0 or row["casual"] + row["registered"] != row["cnt"]:
                raise ValueError(f"第 {number} 行需求总量或 casual+registered=cnt 核对失败")
            if not all(np.isfinite(row[name]) for name in ("temp", "atemp", "hum", "windspeed")):
                raise ValueError(f"第 {number} 行含非有限天气值")
            rows.append(row)
    rows.sort(key=lambda row: row["datetime"])
    if not rows:
        raise ValueError("数据没有记录")
    times = [row["datetime"] for row in rows]
    duplicate_hours = len(times) - len(set(times))
    if duplicate_hours:
        raise ValueError("同一日期小时重复；先核对数据版本")
    span = int((times[-1] - times[0]).total_seconds() / 3600) + 1
    audit = {"source_kind": "synthetic-fixture" if allow_fixture else "real-observational-data",
             "rows": len(rows), "columns": 17, "first_datetime": times[0].isoformat(),
             "last_datetime": times[-1].isoformat(), "duplicate_hours": duplicate_hours,
             "empty_fields": 0, "hours_in_timestamp_span": span,
             "absent_timestamp_rows": span-len(rows),
             "absent_timestamp_policy": "Only counted; no zero-demand rows invented.",
             "sha256": data_hash, "target_identity_check": "casual+registered=cnt in every row",
             "audit_scope": "File integrity and schema, not test target distributions or test scores."}
    return rows, audit


def split_data(rows: list[dict], config: dict) -> dict[str, list[dict]]:
    first = datetime.fromisoformat(config["train_end"])
    second = datetime.fromisoformat(config["validation_end"])
    result = {"train": [], "validation": [], "test": []}
    for row in rows:
        key = "train" if row["datetime"] < first else "validation" if row["datetime"] < second else "test"
        result[key].append(row)
    if any(not values for values in result.values()):
        raise ValueError("固定日期切分后存在空集合")
    return result


def features(rows: list[dict], kind: str, hour_shift: int = 0) -> tuple[np.ndarray, list[str]]:
    """固定类别字典；参照类别 hr=0、weekday=0、month=1、weather=1 省略。"""
    if kind not in {"hour_numeric", "hour_onehot", "workingday_interaction"}:
        raise ValueError("未知特征表示")
    hours = np.asarray([(row["hr"] + hour_shift) % 24 for row in rows], dtype=float)
    work = np.asarray([row["workingday"] for row in rows], dtype=float)
    values, names = [], []
    if kind == "hour_numeric":
        values.append(hours)
        names.append("hr_numeric")
    else:
        for h in range(1, 24):
            values.append((hours == h).astype(float))
            names.append(f"hr_{h}")
    for field, categories in (("weekday", range(1, 7)), ("mnth", range(2, 13)),
                              ("weathersit", range(2, 5))):
        for category in categories:
            values.append(np.asarray([float(row[field] == category) for row in rows]))
            names.append(f"{field}_{category}")
    for field in ("yr", "holiday", "workingday", "temp", "hum", "windspeed"):
        values.append(np.asarray([row[field] for row in rows], dtype=float))
        names.append(field)
    if kind == "workingday_interaction":
        for h in range(1, 24):
            values.append((hours == h).astype(float) * work)
            names.append(f"hr_{h}_x_workingday")
    return np.column_stack(values), names


def fit(train: list[dict], kind: str, alpha: float = 0.0) -> dict:
    if alpha != 0:
        raise ValueError("本课只使用普通最小二乘，alpha=0")
    x, names = features(train, kind)
    center, scale = x.mean(axis=0), x.std(axis=0, ddof=0)
    scale = np.where(scale == 0, 1.0, scale)
    design = np.column_stack([np.ones(len(x)), (x-center)/scale])
    target = np.asarray([row["cnt"] for row in train], dtype=float)
    weights, _, rank, _ = np.linalg.lstsq(design, target, rcond=None)
    # lstsq is defined even for redundant calendar columns; coefficients are not causal effects.
    return {"kind": kind, "feature_names": names, "center": center, "scale": scale,
            "weights": weights, "ridge_alpha": alpha, "train_rows": len(train),
            "design_rank": int(rank), "design_columns": design.shape[1],
            "solver": "numpy.linalg.lstsq; rcond=None", "scale_ddof": 0,
            "intercept_in_weights": "weights[0]; remaining weights follow feature_names"}


def predict(model: dict, rows: list[dict], hour_shift: int = 0) -> np.ndarray:
    x, names = features(rows, model["kind"], hour_shift)
    if names != model["feature_names"]:
        raise ValueError("特征名称与已拟合模型不一致")
    design = np.column_stack([np.ones(len(x)), (x-model["center"])/model["scale"]])
    return np.maximum(0.0, design@model["weights"])


def is_commute(row: dict) -> bool:
    return row["workingday"] == 1 and row["hr"] in COMMUTE_HOURS


def metrics(actual: np.ndarray, prediction: np.ndarray) -> dict:
    if len(actual) == 0:
        return {"n": 0, "mae": None, "rmse": None, "p90_absolute_error": None,
                "p95_absolute_error": None, "mean_signed_error": None, "status": "unavailable"}
    signed = prediction-actual
    absolute = np.abs(signed)
    return {"n": len(actual), "mae": float(absolute.mean()), "rmse": float(np.sqrt((signed**2).mean())),
            "p90_absolute_error": float(np.quantile(absolute, .9, method="linear")),
            "p95_absolute_error": float(np.quantile(absolute, .95, method="linear")),
            "mean_signed_error": float(signed.mean()), "status": "available"}


def method_metrics(rows: list[dict], prediction: np.ndarray) -> dict:
    actual = np.asarray([row["cnt"] for row in rows], dtype=float)
    mask = np.asarray([is_commute(row) for row in rows], dtype=bool)
    total, commute = metrics(actual, prediction), metrics(actual[mask], prediction[mask])
    return {**total, "overall_mae": total["mae"], "commute_mae": commute["mae"],
            "commute_n": commute["n"]}


def record_rows(rows: list[dict], predictions: dict, split: str, threshold: float) -> list[dict]:
    records = []
    for method, values in predictions.items():
        for row, prediction in zip(rows, values, strict=True):
            records.append({"datetime": row["datetime"].isoformat(sep=" "), "split": split,
                            "cnt": row["cnt"], "hr": row["hr"], "workingday": row["workingday"],
                            "mnth": row["mnth"], "season": f"season_{row['season']}",
                            "weathersit": row["weathersit"], "is_commute": is_commute(row),
                            "is_high_demand": row["cnt"] >= threshold, "method": method,
                            "prediction": float(prediction), "err_signed": float(prediction-row["cnt"]),
                            "err_absolute": float(abs(prediction-row["cnt"]))})
    return records


def group_reports(rows: list[dict], predictions: dict, split: str, threshold: float) -> list[dict]:
    groups = [("all", "all", lambda row: True)]
    groups += [("hour", str(h), lambda row, h=h: row["hr"] == h) for h in range(24)]
    groups += [("commute", label, lambda row, yes=yes: is_commute(row) == yes)
               for label, yes in (("commute", True), ("other", False))]
    groups += [("workingday", str(w), lambda row, w=w: row["workingday"] == w) for w in range(2)]
    groups += [("month", str(m), lambda row, m=m: row["mnth"] == m) for m in range(1, 13)]
    groups += [("season", f"season_{s}", lambda row, s=s: row["season"] == s) for s in range(1, 5)]
    groups += [("weather", str(w), lambda row, w=w: row["weathersit"] == w) for w in range(1, 5)]
    groups += [("demand_tail", label, lambda row, yes=yes: (row["cnt"] >= threshold) == yes)
               for label, yes in (("high", True), ("other", False))]
    actual = np.asarray([row["cnt"] for row in rows], dtype=float)
    output = []
    for dimension, label, predicate in groups:
        mask = np.asarray([predicate(row) for row in rows], dtype=bool)
        for method, values in predictions.items():
            output.append({"split": split, "dimension": dimension, "group": label,
                           "method": method, **metrics(actual[mask], values[mask])})
    return output


def text_field(value, field: str) -> str:
    if not isinstance(value, str) or len(value.strip()) < 8 or any(t in value for t in ("待填写", "在这里填写", "YOUR_")):
        raise ValueError(f"{field} 请亲自写至少 8 个字符的具体解释；不能保留模板提示")
    return value.strip()


def verify_preregister(path: Path | None, config: dict) -> dict:
    if path is None:
        raise ValueError("验证运行前必须提供 --preregister：先生成、填写并保存事前实验计划 JSON")
    plan = read_json(path)
    if set(plan) != PREREG_FIELDS or type(plan.get("schema_version")) is not int or plan["schema_version"] != 1:
        raise ValueError("事前实验计划字段不完整；使用 preregister 子命令生成本课模板，保留字段名")
    if plan["change"] != config["change"] or plan["config_sha256"] != digest(config):
        raise ValueError("事前实验计划的候选或配置哈希不一致；先确定配置，再重新生成并填写事前实验计划")
    if plan["primary_metric"] not in {"overall_mae", "commute_mae"}:
        raise ValueError("primary_metric 应亲自选择 overall_mae 或 commute_mae")
    for name in ("hypothesis", "explanation", "check_reason"):
        text_field(plan[name], name)
    rule = plan["check_rule"]
    if not isinstance(rule, dict) or set(rule) != {"minimum_primary_improvement", "maximum_secondary_mae_increase"}:
        raise ValueError("check_rule 需含 minimum_primary_improvement 和 maximum_secondary_mae_increase")
    for name, value in rule.items():
        if type(value) not in (int, float) or not np.isfinite(value) or value < 0:
            raise ValueError(f"{name} 应由你设为非负有限数值，单位为次租借/小时")
    return plan


def preregister_draft(config: dict) -> dict:
    return {"schema_version": 1, "change": config["change"], "config_sha256": digest(config),
            "primary_metric": "", "hypothesis": "", "explanation": "",
            "check_rule": {"minimum_primary_improvement": None, "maximum_secondary_mae_increase": None},
            "check_reason": ""}


def selection_check(plan: dict, scores: dict) -> dict:
    primary = plan["primary_metric"]
    secondary = "commute_mae" if primary == "overall_mae" else "overall_mae"
    original, candidate = scores["original"], scores["candidate"]
    if any(scores[m][k] is None for m in ("original", "candidate") for k in (primary, secondary)):
        raise ValueError("验证集的主要或次要组没有记录，无法检验事先规则")
    improvement = original[primary]-candidate[primary]
    increase = candidate[secondary]-original[secondary]
    rule = plan["check_rule"]
    passes = improvement > rule["minimum_primary_improvement"] and increase <= rule["maximum_secondary_mae_increase"]
    return {"primary_metric": primary, "secondary_metric": secondary,
            "primary_improvement_original_minus_candidate": improvement,
            "secondary_increase_candidate_minus_original": increase,
            "rule": rule, "candidate_passes": bool(passes),
            "interpretation": "Candidate must improve primary by MORE than the minimum and keep secondary increase at most the limit."}


def source_hashes(root: Path) -> dict:
    return {name: sha256(root/name) for name in SOURCE_FILES}


def verify_validation(root: Path, reviewed: Path, config: dict | None = None, data_hash: str | None = None) -> tuple[dict, dict]:
    manifest = read_json(reviewed/"source_manifest.json")
    old_config = read_json(reviewed/"config-used.json")
    if manifest.get("evaluation_mode") != "validation" or not manifest.get("test_sealed"):
        raise ValueError("决策必须引用已保存的验证运行；不能引用测试运行")
    if config is not None and (old_config != config or manifest.get("resolved_config_sha256") != digest(config)):
        raise ValueError("决策引用的验证配置与当前配置不一致")
    if data_hash is not None and manifest.get("data_sha256") != data_hash:
        raise ValueError("决策引用的验证数据与当前数据不一致")
    if manifest.get("source_sha256") != source_hashes(root):
        raise ValueError("验证后程序已改变，需重新验证并保存决策")
    expected_files = VALIDATION_ARTIFACTS - {"source_manifest.json"}
    hashes = manifest.get("artifact_sha256", {})
    if set(hashes) != expected_files:
        raise ValueError("验证运行的产物清单不完整")
    for name, expected in hashes.items():
        if sha256(reviewed/name) != expected:
            raise ValueError(f"验证产物 {name} 已被修改，请重新运行；不要手改结果")
    plan = verify_preregister(reviewed/"preregister-used.json", old_config)
    result = read_json(reviewed/"metrics.json")
    computed = selection_check(plan, result["metrics"]["validation"])
    if result.get("selection_check") != computed:
        raise ValueError("保存的验证比较与事前实验计划规则不一致")
    return manifest, result


def decision_draft(root: Path, reviewed: Path) -> dict:
    verify_validation(root, reviewed)
    return {"selected_method": "", "reason": "", "reviewed_validation_run": str(reviewed.relative_to(root)),
            "validation_manifest_sha256": sha256(reviewed/"source_manifest.json")}


def verify_decision(root: Path, path: Path | None, config: dict, data_hash: str) -> dict:
    if path is None:
        raise ValueError("打开测试前必须提供 --decision：先根据验证运行保存选择和理由")
    decision = read_json(path)
    if set(decision) != DECISION_FIELDS:
        raise ValueError("决策字段不完整；使用 decision 子命令从保存的验证运行生成模板")
    if decision["selected_method"] not in {"original", "candidate"}:
        raise ValueError("selected_method 先根据验证选择 original 或 candidate")
    text_field(decision["reason"], "reason")
    if not isinstance(decision["reviewed_validation_run"], str):
        raise ValueError("reviewed_validation_run 应为验证结果目录")
    reviewed = safe_path(root, decision["reviewed_validation_run"])
    _, result = verify_validation(root, reviewed, config, data_hash)
    if decision["validation_manifest_sha256"] != sha256(reviewed/"source_manifest.json"):
        raise ValueError("决策引用的验证清单哈希不一致，需根据这次验证重新生成决策")
    if decision["selected_method"] == "candidate" and not result["selection_check"]["candidate_passes"]:
        raise ValueError("候选未通过你事先写下的规则，请保留 original；要改规则需承认探索并重新保存事前实验计划")
    return {**decision, "decision_file": str(path.relative_to(root)), "decision_sha256": sha256(path)}


def serializable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(item) for item in value]
    return value


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(serializable(value), ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def write_new_json(path: Path, value) -> None:
    if path.exists():
        raise ValueError("输出文件已经存在，请使用新路径，保留以前的证据")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(serializable(value), ensure_ascii=False, indent=2, allow_nan=False)+"\n")


def write_csv(path: Path, rows: list[dict], columns: list[str] | None = None) -> None:
    if not rows:
        raise ValueError("输出表没有记录")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_bike(root: Path, config_path: Path, output: Path, *, preregister_path: Path | None = None,
             unlock_test: bool = False, decision_path: Path | None = None, allow_fixture: bool = False,
             replace_default: bool = False) -> None:
    if replace_default and (output != safe_path(root, "lesson-08/artifacts/run") or unlock_test):
        raise ValueError("受控重算仅用于默认验证目录；最后测试请指定新的 --output")
    if output.exists() and not replace_default:
        raise ValueError("结果目录已经存在，请使用新 --output，保留以前的比较证据")
    if output.exists() and replace_default:
        if not output.is_dir() or output.is_symlink() or any(
            p.name not in VALIDATION_ARTIFACTS or not p.is_file() or p.is_symlink() for p in output.iterdir()
        ):
            raise ValueError("默认结果目录含非运行产物，不能覆盖；请保留文件并指定新的 --output")
    config = config_from(config_path)
    if decision_path and not unlock_test:
        raise ValueError("--decision 不会自动打开测试；需明确加 --unlock-test")
    if preregister_path and unlock_test:
        raise ValueError("测试从引用的验证运行读取事前实验计划，不使用新的 --preregister")
    plan = verify_preregister(preregister_path, config) if not unlock_test else None
    rows, audit = load_data(safe_path(root, config["data"]), allow_fixture)
    splits = split_data(rows, config)
    counts = {name: len(group) for name, group in splits.items()}
    if not allow_fixture and counts != {"train": 13003, "validation": 2208, "test": 2168}:
        raise ValueError("正式数据的固定日期切分数量与核定版本不一致")
    decision = verify_decision(root, decision_path, config, audit["sha256"]) if unlock_test else None
    kinds = {"original": "hour_numeric" if config["change"] == "hour_onehot" else "hour_onehot",
             "candidate": config["change"]}
    methods = [decision["selected_method"]] if decision else ["original", "candidate"]
    models = {name: fit(splits["train"], kinds[name]) for name in methods}
    threshold = float(np.quantile([r["cnt"] for r in splits["train"]], config["tail_quantile"], method="linear"))
    records, groups, summaries = [], [], {}
    for split in (["test"] if unlock_test else ["train", "validation"]):
        sample = splits[split]
        predictions = {name: predict(models[name], sample) for name in methods}
        summaries[split] = {name: method_metrics(sample, values) for name, values in predictions.items()}
        records.extend(record_rows(sample, predictions, split, threshold))
        groups.extend(group_reports(sample, predictions, split, threshold))
    focus = "test" if unlock_test else "validation"
    # Include equally many large-error records per method; the two methods stay distinguishable.
    error_cases = []
    for method in methods:
        subset = [r for r in records if r["split"] == focus and r["method"] == method]
        error_cases.extend(sorted(subset, key=lambda r: (-r["err_absolute"], r["datetime"]))[:config["error_case_count"]])
    sample = splits[focus]
    condition = {"description": "模拟小时登记偏移；固定模型、实际需求和其他字段，诊断输入敏感性，不是改变时间的因果效果。",
                 "split": focus, "shift_hours": config["condition_hour_shift"], "model_refit": False,
                 "metrics": {name: method_metrics(sample, predict(models[name], sample, config["condition_hour_shift"])) for name in methods}}
    audit["split_counts"] = counts
    audit["weather_category_counts_by_split"] = {key: {str(w): sum(r["weathersit"] == w for r in group) for w in range(1,5)}
                                                for key, group in splits.items()}
    result = {"lesson": "lesson-08", "status": "experiment_evidence_not_student_conclusion",
              "target": "cnt: recorded hourly rentals; not unmet demand or a causal effect",
              "unit": "次租借/已记录小时", "condition": "Given actual weather in the SAME hour; not known future weather.",
              "change": config["change"], "method_kinds": {name: kinds[name] for name in methods},
              "split_counts": counts, "train_end_exclusive": config["train_end"],
              "validation_end_exclusive": config["validation_end"], "evaluation_mode": focus,
              "test_sealed": not unlock_test,
              "commute_definition": {"workingday": 1, "hours": COMMUTE_HOURS,
                  "meaning": "Teaching-defined working-day hour group; not observed commuter identities."},
              "prediction_rule": "Negative predictions clipped to 0 identically for both models.",
              "tail_threshold": {"trained_on": "train", "quantile": config["tail_quantile"],
                                 "cnt_at_least": threshold, "quantile_method": "linear"},
              "metrics": summaries,
              "selection_check": selection_check(plan, summaries["validation"]) if plan else None}
    comparison = [{"split": split, "method": name, "kind": kinds[name],
                   "n": m["n"], "overall_mae": m["overall_mae"], "commute_n": m["commute_n"],
                   "commute_mae": m["commute_mae"]} for split, scores in summaries.items() for name, m in scores.items()]
    # Only the reproducible default validation directory can replace known generated files.
    # Explicit output paths always remain immutable. No student-authored files are removed.
    if replace_default and output.exists():
        for path in output.iterdir():
            path.unlink()
    output.mkdir(parents=True, exist_ok=replace_default)
    write_json(output/"metrics.json", result)
    write_json(output/"summary.json", result)
    write_json(output/"config-used.json", config)
    if plan:
        write_json(output/"preregister-used.json", plan)
    else:
        write_json(output/"decision-used.json", decision)
    write_json(output/"data_audit.json", audit)
    write_json(output/"models.json", models)
    write_json(output/"condition_check.json", condition)
    write_csv(output/"comparison.csv", comparison)
    write_csv(output/"records.csv", records, RECORD_COLUMNS)
    write_csv(output/"group_metrics.csv", groups)
    write_csv(output/"error_cases.csv", error_cases, RECORD_COLUMNS)
    # One working-day rush-hour row, when available, exposes every arithmetic step.
    trace_row = next((row for row in sample if is_commute(row)), sample[0])
    trace = []
    for name, model in models.items():
        x, names = features([trace_row], model["kind"])
        z = (x[0]-model["center"])/model["scale"]
        raw_prediction = float(model["weights"][0] + z@model["weights"][1:])
        entries = [("intercept", 1.0, 0.0, 1.0, 1.0, float(model["weights"][0]))]
        entries += [(field, float(raw), float(center), float(scale), float(standardized), float(weight))
                    for field, raw, center, scale, standardized, weight in
                    zip(names, x[0], model["center"], model["scale"], z, model["weights"][1:], strict=True)]
        for field, raw, center, scale, standardized, weight in entries:
            trace.append({"datetime": trace_row["datetime"].isoformat(sep=" "), "split": focus,
                          "method": name, "feature": field, "raw_feature": raw,
                          "training_mean": center, "training_scale": scale,
                          "standardized_feature": standardized, "weight": weight,
                          "contribution": standardized*weight, "raw_prediction": raw_prediction,
                          "clipped_prediction": max(0.0, raw_prediction), "cnt": trace_row["cnt"]})
    write_csv(output/"feature_trace.csv", trace)
    artifact_files = sorted(p.name for p in output.iterdir() if p.is_file())
    manifest = {"data_file": config["data"], "data_sha256": audit["sha256"],
                "source_sha256": source_hashes(root), "config_file": str(config_path.relative_to(root)),
                "config_sha256": sha256(config_path), "resolved_config_sha256": digest(config),
                "evaluation_mode": focus, "data_kind": audit["source_kind"],
                "python": platform.python_version(), "numpy": np.__version__, "test_sealed": not unlock_test,
                "preregister_file": str(preregister_path.relative_to(root)) if preregister_path else None,
                "preregister_sha256": sha256(preregister_path) if preregister_path else None,
                "decision": decision, "artifact_sha256": {name: sha256(output/name) for name in artifact_files}}
    # No wall-clock times in scientific artifacts: exact same inputs can be replayed byte for byte.
    write_json(output/"source_manifest.json", manifest)
    if allow_fixture:
        print("仅合成测试夹具：验证程序接口，不能当作真实数据实验结果。")
    print(f"结果写入：{output.relative_to(root)}；先打开 comparison.csv")
    for name, values in summaries[focus].items():
        print(f"{focus}/{name}: n={values['n']}, overall MAE={values['overall_mae']:.3f}, commute MAE={values['commute_mae']:.3f} 次租借/小时")
    print("测试尚未评价。先解释验证错误，再保存决策。" if not unlock_test else
          "仅评价事先选定方案；测试后修改属于新一轮开发，需要新测试证据。")


def run_warmup(root: Path, output: Path) -> None:
    """旧 24 行人工数据只取 12 行训练期做短追踪，不自动跑完整旧实验。"""
    if output.exists():
        raise ValueError("结果目录已经存在，请使用新 --output")
    data_path = root/"lesson-08/data/base.json"
    rows = read_json(data_path)["rows"]
    train = [r for r in rows if r["split"] == "train"]
    known = [r["queue_length"] for r in train if r["queue_length"] is not None]
    fill = float(np.mean(known))
    records = []
    for row in train:
        x = fill if row["queue_length"] is None else row["queue_length"]
        pred = 1+2*x
        records.append({"id": row["id"], "split": "train", "queue_length_raw": row["queue_length"],
                        "queue_length_used": x, "fixed_rule_prediction": pred, "wait_minutes": row["wait_minutes"],
                        "err_absolute": abs(pred-row["wait_minutes"])})
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output/"records.csv", records)
    write_json(output/"summary.json", {"kind": "synthetic-short-warmup", "source_rows": len(rows),
               "training_rows_used": len(train), "known_queue_training_rows": len(known),
               "training_queue_sum": sum(known), "fill_training_mean": fill,
               "fixed_rule": "prediction=1+2*queue_length_used; given teaching rule, not fitted",
               "unit": "分钟", "test_evaluated": False, "data_sha256": sha256(data_path)})
    print(f"短热身写入：{output.relative_to(root)}；只用 {len(train)} 行人工训练样本，真实任务仍需事前实验计划。")
