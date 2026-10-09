"""开放研究的数据起点：读取、核对和薄计算工具，不运行整课答案。

公开原始 CSV 可由学生读取；测试期封存是研究协议。本 reader 不返回
测试期标签，不能将它描述成对公开数据实现了技术上不可绕过的访问控制。
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

OFFICIAL_SHA256 = "e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f"
TRAIN_END = "2012-07-01"
VALIDATION_END = "2012-10-01"
SOURCE_FIELDS = ["instant", "dteday", "season", "yr", "mnth", "hr", "holiday", "weekday",
                 "workingday", "weathersit", "temp", "atemp", "hum", "windspeed", "casual", "registered", "cnt"]
FLOAT_FIELDS = {"temp", "atemp", "hum", "windspeed"}
BASELINE_LESSONS = {1, 2, 3, 6, 7}
STARTER_FILES = {"audit.json", "summary.json", "config_snapshot.json", "sample.csv",
                 "baseline.json", "manual_sample.csv", "split_manifest.csv"}


def _json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def _root_path(root, name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("路径须为非空字符串")
    path = (Path(root) / name).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("起点读写路径须位于学生仓库内")
    return path


def _lesson_path(root, lesson_dir, name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("路径须为非空字符串")
    value = Path(name)
    first = value.parts[0]
    prefix = first.startswith("lesson-") and first[7:].isdigit()
    base = Path(root) if value.is_absolute() or prefix else Path(lesson_dir)
    return _root_path(root, str(base / value))


def _read_source(root, data, include_test=False):
    path = _root_path(root, data)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != OFFICIAL_SHA256:
        raise ValueError("这份 Bike 原始 CSV 与随包官方字节不符；请保留原件。自选其他数据时自行编写相应 reader")
    train, validation, metadata, test = [], [], [], []
    empty_fields = 0
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != SOURCE_FIELDS:
            raise ValueError("Bike 表头应为官方顺序的 17 列")
        for line, raw in enumerate(reader, 2):
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"第 {line} 行缺列，先核对原文件")
            empty_fields += sum(not value.strip() for value in raw.values())
            # 封存行只解析元数据，不解析 cnt/casual/registered，也不传回目标。
            try:
                hour = int(raw["hr"])
                stamp = (datetime.strptime(raw["dteday"], "%Y-%m-%d") + timedelta(hours=hour)).isoformat(timespec="minutes")
                instant = int(raw["instant"])
            except (ValueError, TypeError) as error:
                raise ValueError(f"第 {line} 行日期/小时/编号无法读取") from error
            if not 0 <= hour <= 23:
                raise ValueError(f"第 {line} 行 hr 应在 0–23")
            partition = "train" if stamp < TRAIN_END else "validation" if stamp < VALIDATION_END else "sealed_test"
            metadata.append({"instant": instant, "datetime": stamp, "hr": hour, "partition": partition})
            if partition == "sealed_test" and not include_test:
                continue
            try:
                row = {field: raw[field] if field == "dteday" else float(raw[field]) if field in FLOAT_FIELDS
                       else int(raw[field]) for field in SOURCE_FIELDS}
            except (ValueError, TypeError) as error:
                raise ValueError(f"开发数据第 {line} 行数值无法读取") from error
            if not all(np.isfinite(row[field]) for field in FLOAT_FIELDS):
                raise ValueError(f"开发数据第 {line} 行天气数值非有限")
            row["datetime"] = stamp
            (train if partition == "train" else validation if partition == "validation" else test).append(row)
    metadata.sort(key=lambda row: row["datetime"])
    train.sort(key=lambda row: row["datetime"])
    validation.sort(key=lambda row: row["datetime"])
    if not train or not validation:
        raise ValueError("开发切分为空，请核对官方原件")
    timestamps = {row["datetime"] for row in metadata}
    first = datetime.fromisoformat(metadata[0]["datetime"])
    last = datetime.fromisoformat(metadata[-1]["datetime"])
    expected = int((last - first).total_seconds() // 3600) + 1
    observed_month = Counter(row["datetime"][:7] for row in metadata)
    expected_month = Counter()
    current = first
    while current <= last:
        expected_month[current.strftime("%Y-%m")] += 1
        current += timedelta(hours=1)
    audit = {"data_sha256": digest, "rows": len(metadata), "columns": len(SOURCE_FIELDS),
             "source_fields": SOURCE_FIELDS, "empty_fields": empty_fields,
             "duplicate_hours": len(metadata) - len(timestamps), "expected_calendar_hours": expected,
             "absent_timestamp_rows": expected - len(timestamps),
             "absent_timestamp_policy": "缺少的小时只计数，不补为需求 0",
             "first_datetime": metadata[0]["datetime"], "last_datetime": metadata[-1]["datetime"],
             "training_rows": len(train), "validation_rows": len(validation),
             "sealed_test_rows": sum(row["partition"] == "sealed_test" for row in metadata),
             "training_end_exclusive": TRAIN_END, "validation_end_exclusive": VALIDATION_END,
             "monthly_coverage": [{"month": month, "expected_hours": expected_month[month],
                                   "observed_rows": observed_month[month],
                                   "missing_hours": expected_month[month] - observed_month[month]}
                                  for month in sorted(expected_month)],
             "target_policy": "audit 仅文件/日历元数据；返回开发集标签供学生自行研究，不返回封存测试标签"}
    return train, validation, audit, metadata, test


def load_development(root, data="data/bike/hour.csv"):
    """返回 train, validation, audit；日期为 ISO 字符串，其他数值为 int/float。"""
    train, validation, audit, _, _ = _read_source(Path(root).resolve(), data)
    return train, validation, audit


def load_test(root, decision_path, data="data/bike/hour.csv"):
    """学生验证后明确调用；只核对已保存非空决定文件，不判断研究结论。

    decision_path 相对于学生根，可为任意自由文字/JSON。学生须先写清选择、
    理由及预期，再最后评价测试结果。公开 CSV 可绕过此函数读取，故这是
    研究纪律与人工核查协议，不宣称技术上强制封存或能自动证明预先登记。
    """
    root = Path(root).resolve()
    path = _root_path(root, str(decision_path))
    if not path.is_file():
        raise ValueError("先在学生仓库内保存自己的验证后决定，再明确调用 load_test")
    if not path.read_text(encoding="utf-8").strip():
        raise ValueError("决定文件为空；先写出选定方案、理由和预期，不用空文件代替选择")
    _, _, _, _, test = _read_source(root, data, include_test=True)
    return test


# 名称同时提醒调用者：这是验证后自己已经选定方案的最终评价读取。
load_selected_test = load_test


def _finite_sequence(values, name):
    try:
        result = np.asarray(list(values), dtype=float)
    except (ValueError, TypeError) as error:
        raise ValueError(f"{name} 须为一列数值") from error
    if result.ndim != 1 or result.size == 0 or not np.all(np.isfinite(result)):
        raise ValueError(f"{name} 须为非空的一列有限数值")
    return result


def mae(actual, predicted):
    """只核算学生提供的等长两列；不自动选择样本、方法或评价用途。"""
    actual = _finite_sequence(actual, "actual")
    predicted = _finite_sequence(predicted, "predicted")
    if len(actual) != len(predicted):
        raise ValueError("actual 与 predicted 须等长，逐条对应同一样本")
    value = float(np.mean(np.abs(actual - predicted)))
    if not np.isfinite(value):
        raise ValueError("误差计算数值溢出，请核对数值尺度")
    return value


def fit_simple_line(x, y):
    """仅拟合学生给定的一个输入与标签，返回 (intercept, slope)。"""
    x, y = _finite_sequence(x, "x"), _finite_sequence(y, "y")
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("x 与 y 须等长且至少两条，只传入你选定的训练数据")
    centered = x - np.mean(x)
    denominator = float(np.dot(centered, centered))
    if denominator == 0:
        raise ValueError("训练输入没有变化，不能据此学习直线斜率；可考虑均值基线")
    slope = float(np.dot(centered, y - np.mean(y)) / denominator)
    intercept = float(np.mean(y) - slope * np.mean(x))
    if not np.isfinite(intercept) or not np.isfinite(slope):
        raise ValueError("直线拟合数值溢出，请核对输入尺度")
    return intercept, slope


def write_csv(path, rows, fieldnames=None):
    """保存学生自行构造的字典行；空行集合须提供 fieldnames。"""
    path = Path(path)
    rows = list(rows)
    if fieldnames is None:
        if not rows:
            raise ValueError("空 CSV 需要 fieldnames 才能保存表头")
        fieldnames = list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def save_results(output_dir, records, summary, fieldnames=None):
    """把学生自己的 records/summary 保存到新目录，不拟合或决定研究流程。"""
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise ValueError("结果目录已存在；选新目录以保留证据")
    text = _json_text(summary)
    records = list(records)
    if not records and fieldnames is None:
        raise ValueError("没有记录时须给 fieldnames，不用空结果冒充完成")
    output_dir.mkdir(parents=True, exist_ok=False)
    write_csv(output_dir / "records.csv", records, fieldnames)
    (output_dir / "summary.json").write_text(text, encoding="utf-8")


def main(lesson_dir, lesson_number):
    lesson_dir = Path(lesson_dir).resolve()
    root = lesson_dir.parent
    if type(lesson_number) is not int or not 1 <= lesson_number <= 7:
        raise ValueError("这个主起点用于 01–07；08 由本课开放入口处理")
    parser = argparse.ArgumentParser(description="准备真实 Bike 开发数据；请自行完成研究程序与证据")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        config_path = _lesson_path(root, lesson_dir, args.config)
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("config 顶层须为 JSON 对象；可留空对象并自行添加实验字段")
        enabled = config.get("starter_baseline", lesson_number == 2)
        if type(enabled) is not bool:
            raise ValueError("starter_baseline 若使用，应为 true 或 false；其余开放字段留给你的程序")
        output = _lesson_path(root, lesson_dir, args.output or "artifacts/starter")
        if args.output is not None and output.exists():
            raise ValueError("显式输出目录已存在；请使用新名称保留每次研究证据")
        train, validation, audit, metadata, _ = _read_source(root, config.get("data", "data/bike/hour.csv"))
        sample = [{**row, "partition": partition} for partition, values in (("train", train), ("validation", validation))
                  for row in values[:6]]
        if lesson_number in (4, 5):
            sample = [row for row in metadata if row["partition"] == "train"][:6] + [row for row in metadata if row["partition"] == "validation"][:6]
        summary = {"status": "not_started", "prepared": True, "lesson": lesson_number,
                   "training_rows": len(train), "validation_rows": len(validation),
                   "sealed_test_rows": audit["sealed_test_rows"], "data_sha256": audit["data_sha256"],
                   "sample_rows": len(sample), "sample_purpose": "只预览结构；不代替完整开发数据",
                   "completion_note": "仅完成数据起点；自己实现重要选择、运行实验、保存证据并完成解释后才算完成"}
        json_outputs = {"audit.json": audit, "summary.json": summary, "config_snapshot.json": config}
        csv_outputs = {"sample.csv": sample}
        if lesson_number == 5:
            csv_outputs["split_manifest.csv"] = [row for row in metadata if row["partition"] != "sealed_test"]
        if enabled and lesson_number in BASELINE_LESSONS:
            mean = float(np.mean([row["cnt"] for row in train]))
            json_outputs["baseline.json"] = {"method": "training_mean", "training_rows": len(train),
                "prediction": mean, "validation_rows": len(validation),
                "validation_mae": mae([row["cnt"] for row in validation], [mean] * len(validation)),
                "mae_denominator": len(validation), "purpose": "可选简单起点，不是正式方案或候选对比"}
        if lesson_number == 1 and "intercept" in config and "slope" in config:
            intercept, slope = config["intercept"], config["slope"]
            if type(intercept) not in (int, float) or type(slope) not in (int, float) or not np.isfinite(intercept) or not np.isfinite(slope):
                raise ValueError("可选人工示范的 intercept/slope 须为有限数值")
            manual = []
            for row in sample[:3]:
                prediction = max(0.0, intercept + slope * row["temp"])
                if not np.isfinite(prediction):
                    raise ValueError("可选人工示范数值溢出，请缩小参数")
                manual.append({"instant": row["instant"], "datetime": row["datetime"], "temp": row["temp"],
                               "prediction": prediction, "cnt": row["cnt"], "absolute_error": abs(prediction - row["cnt"])})
            csv_outputs["manual_sample.csv"] = manual
        # 先验证所有JSON，失败时不创建一半产物；只清理本起点拥有的过期文件。
        texts = {name: _json_text(value) for name, value in json_outputs.items()}
        output.mkdir(parents=True, exist_ok=args.output is None)
        for name in STARTER_FILES - set(json_outputs) - set(csv_outputs):
            stale = output / name
            if stale.is_file():
                stale.unlink()
        for name, text in texts.items():
            (output / name).write_text(text, encoding="utf-8")
        for name, values in csv_outputs.items():
            write_csv(output / name, values)
    except (ValueError, OSError, TypeError) as error:
        print(f"起点未完成：{error}", file=sys.stderr)
        raise SystemExit(2) from error
    print(f"数据起点已准备：{output}；研究状态仍为 not_started。")
    print("先看 sample.csv 的结构；自行编写实验并保存你选择的方法、结果和解释。")
