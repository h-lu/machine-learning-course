"""命令行入口与结果追溯；不替学生填写结论。"""

from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import platform
from pathlib import Path
import numpy as np
from .experiments import EXPERIMENTS
from .foundations import console_summary as foundations_console_summary


def convert(value):
    if isinstance(value, np.ndarray):
        return convert(value.tolist())
    if isinstance(value, np.generic):
        return convert(value.item())
    if isinstance(value, dict):
        return {str(k): convert(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [convert(v) for v in value]
    if isinstance(value, float):
        if not np.isfinite(value):
            raise ValueError("计算产生非有限值；请检查数据与参数，不应把它保存成成绩")
        return round(value, 10)
    return value


def digest(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()


def source_hashes():
    """记录实际执行的共享源码，避免只保存一个不随代码变化的版本名。"""
    directory = Path(__file__).resolve().parent
    return {
        f"mlcourse/{name}": hashlib.sha256((directory / name).read_bytes()).hexdigest()
        for name in ("runtime.py", "mathops.py", "experiments.py", "intro.py", "foundations.py", "foundations_data.py")
    }


def run_experiment(lesson, data, config):
    if lesson not in EXPERIMENTS:
        raise ValueError(f"没有课次{lesson}")
    if not isinstance(data, dict) or not isinstance(config, dict):
        raise ValueError("数据和配置的顶层必须为对象")
    if not isinstance(config.get("seed"), int) or isinstance(config.get("seed"), bool):
        raise ValueError("seed必须为整数")
    if "rows" in data and (not isinstance(data["rows"], list) or not data["rows"]):
        raise ValueError("rows必须是非空数组")
    # Do not silently accept NaN that the Python JSON parser otherwise permits.
    digest(data)
    digest(config)
    result = EXPERIMENTS[lesson](data, config)
    return convert(
        {
            "lesson": lesson,
            "status": "example_only",
            "data": {
                "kind": data.get("kind"),
                "source": data.get("source"),
                "rows": len(data["rows"]) if "rows" in data else None,
            },
            "config": config,
            **result,
            "provenance": {
                "data_sha256": digest(data),
                "config_sha256": digest(config),
                "source_sha256": source_hashes(),
                "runtime": "mlcourse-numpy-v2",
                "python": platform.python_version(),
                "numpy": np.__version__,
            },
        }
    )



def intro_console_summary(result):
    """按入门阅读顺序展示结果；不改变结果接口，也不替学生选择模型。"""
    detail = result["details"]
    names = {"rule": "人工规则", "baseline": "均值基线", "linear": "一元线性回归"}
    split_names = {"train": "给定样本（不训练）", "validation": "验证集", "test": "测试集"}
    reports = {detail["primary_model"]: result["metrics"], **result["comparison"]}
    lines = [f"评价数据：{split_names[detail['evaluation_split']]}；样本数：{result['metrics']['n']}"]
    if len(reports) == 1:
        lines.append("人工规则参数由人设定；C01 先核对一条预测，不要求读懂所有汇总指标。")
    else:
        lines.append("MAE（平均绝对误差）：单位为分钟；数值越小，表示在这批样本上平均相差越少。")
        for name in ("baseline", "rule", "linear"):
            lines.append(f"{names[name]}：MAE = {reports[name]['mae']:.6g} 分钟")
        lines.append("这些是比较结果，不是自动推荐；metrics 固定保存线性回归指标。")
        lines.append("分组评估（先看每组样本数，再看误差）：")
        for period, group in detail["by_period"].items():
            values = "；".join(f"{names[name]} MAE = {group[name]['mae']:.6g} 分钟"
                               for name in ("baseline", "rule", "linear"))
            lines.append(f"{period}，{group['linear']['n']} 条：{values}")
    rows = detail["predictions"]
    row = next((item for item in rows if item["id"] == "train-03"), rows[min(2, len(rows) - 1)])
    lines.append(f"逐条核对示例 {row['id']}：人数 = {row['queue_length']} 人；实际值 = {row['actual']} 分钟")
    for name in names:
        if name in reports:
            lines.append(f"  {names[name]}预测 = {row[f'prediction_{name}']:.6g} 分钟；"
                         f"绝对误差 = {row[f'absolute_error_{name}']:.6g} 分钟")
    stress = result["stress_test"]["metrics"]
    values = "；".join(f"{names[name]}预测 = {value:.6g} 分钟" for name, value in stress["predictions"].items())
    lines.append(f"新输入检查：{stress['queue_length']} 人；{values}")
    lines.append("没有实际等待时间，不能计算误差；null 表示没有值，不是误差为 0。")
    if stress["outside_training_range"]:
        lines.append("提醒：这个人数超出了给定样本的人数区间，能计算不代表可靠。")
    return "\n".join(lines)


def linear_reading_tables(data, result):
    """S07 的阅读表：由既有结果导出，不重训、不改指标，不混淆人工外推标签。"""
    train = [row for row in data["rows"] if row.get("split") == "train"]
    evaluation = [row for row in data["rows"] if row.get("split") != "train"]
    detail = result["details"]
    baseline = sum(row["target"] for row in train) / len(train)
    lower, upper = min(row["x1"] for row in train), max(row["x1"] for row in train)
    records, extrapolation = [], []
    weights = detail["coefficients"]
    for row, actual, prediction, far, far_actual in zip(
        evaluation, detail["actual"], detail["prediction"],
        detail["extrapolation_x"], detail["extrapolation_actual"], strict=True
    ):
        records.append(dict(id=row["id"], x1=row["x1"], x2=row["x2"], group=row.get("group"),
                            actual=actual, prediction=prediction, baseline_prediction=baseline,
                            residual_actual_minus_prediction=actual-prediction,
                            absolute_error=abs(actual-prediction)))
        extrapolation.append(dict(id=row["id"], original_x1=row["x1"], shifted_x1=far[0], x2=far[1],
                                  prediction=weights[0]+weights[1]*far[0]+weights[2]*far[1],
                                  synthetic_target=far_actual, outside_training_x1=not lower <= far[0] <= upper))
    comparison = [dict(method="linear", method_name="线性回归 / 岭回归", unit="无量纲", **result["metrics"]),
                  dict(method="training_mean", method_name="训练均值基线", unit="无量纲", **result["comparison"]["training_mean"])]
    return convert(dict(comparison=comparison, records=records, extrapolation=extrapolation))


def read_input_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} 第 {error.lineno} 行第 {error.colno} 列的 JSON 格式有误；"
                         "请检查英文双引号、逗号和冒号，最后一项后不加逗号。") from error


def main(lesson_directory):
    parser = argparse.ArgumentParser(
        description="运行本课小实验；结果只作为入门示例，学生自行论证采用方案。"
    )
    parser.add_argument("--config", type=Path, default=lesson_directory / "config.json")
    parser.add_argument(
        "--data", type=Path, default=lesson_directory / "data/base.json"
    )
    parser.add_argument("--output", type=Path, default=lesson_directory / "artifacts")
    parser.add_argument("--split", choices=["validation", "test"], help="C02、S01、S03–S06：选择验证集或测试集；S02 使用观察截止日")
    args = parser.parse_args()
    try:
        data = read_input_json(args.data)
        config = read_input_json(args.config)
        if args.split:
            if lesson_directory.name not in {"C02", "lesson-02", "S01", "S03", "S04", "S05", "S06", "lesson-03", "lesson-05", "lesson-06", "lesson-07", "lesson-08"}:
                raise ValueError("本课不支持 --split；S02 请使用 observation_day 调整标签观察截止日")
            config["evaluation_split"] = args.split
        result = run_experiment(lesson_directory.name, data, config)
        result["provenance"].update(
            {
                "data_file": os.path.relpath(args.data, Path.cwd()),
                "config_file": os.path.relpath(args.config, Path.cwd()),
                "data_file_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
                "config_file_sha256": hashlib.sha256(
                    args.config.read_bytes()
                ).hexdigest(),
                "entry_sha256": hashlib.sha256(
                    (lesson_directory / "analysis.py").read_bytes()
                ).hexdigest(),
            }
        )
        args.output.mkdir(parents=True, exist_ok=True)
        path = args.output / "summary.json"
        path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        records = result["details"].get("predictions")
        if records and isinstance(records[0], dict):
            with (args.output / "predictions.csv").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(records[0]))
                writer.writeheader()
                writer.writerows(records)
            print("逐条预测：", args.output / "predictions.csv")
            if lesson_directory.name in {"C01", "C02", "lesson-01", "lesson-02"}:
                print(intro_console_summary(result))
            else:
                print("评价数据：", result["details"]["evaluation_split"], "；MAE：", result["metrics"]["mae"], "分钟")
        tables = result["details"].get("tables", {})
        for name, table in tables.items():
            if not table:
                continue
            fields = list(dict.fromkeys(key for record in table for key in record))
            csv_path = args.output / f"{name}.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(table)
            print(f"表格：{csv_path}")
        if tables:
            print(foundations_console_summary(result))
        if lesson_directory.name in {"S07", "lesson-09"}:
            for name, table in linear_reading_tables(data, result).items():
                csv_path = args.output / f"{name}.csv"
                with csv_path.open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(table[0]))
                    writer.writeheader()
                    writer.writerows(table)
                print(f"阅读表格：{csv_path}")
            print("S07：特征与目标均无量纲；evaluation 用于开发评价，不是未见最终测试。")
            print("先看 comparison.csv 的方法名和 MAE，再从 records.csv 核对真实值减预测值。")
            print("extrapolation.csv 的 synthetic_target 是人工对照标签，不是实际观测。")
        print(f"{lesson_directory.name}: 示例实验已运行，结果写入 {path}")
    except (ValueError, KeyError, TypeError, IndexError, OSError) as error:
        parser.exit(
            2,
            f"无法运行：{error}\n请检查数据说明、字段和参数。已有结果文件可能来自以前的运行，不能作为本次结果；修正后重新运行。\n",
        )
