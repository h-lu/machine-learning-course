"""第8课开放起点：开发数据审计与训练均值基线；候选由学生自行构建。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LESSON = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from mlcourse.bike_starter import load_development, mae, write_csv

# 预测时可用的字段。目标及其组成项、记录编号不传给候选的评价输入。
INPUT_FIELDS = ("dteday", "datetime", "season", "yr", "mnth", "hr", "holiday",
                "weekday", "workingday", "weathersit", "temp", "atemp", "hum", "windspeed")
OUTPUT_FILES = ("summary.json", "comparison.csv", "records.csv", "data_audit.json")


def candidate_predictions(train_inputs, train_targets, evaluation_inputs):
    """在这里实现自己计划的一项候选，也可另写研究入口。

    三个参数：训练输入字典列表、训练 cnt 数值列表、评价输入字典列表。
    返回与评价输入等长的有限数值预测列表，或 {自定方法名: 预测列表}。
    不要在评价输入查找真实 cnt。
    默认 None 表示没有候选，所以起点只跑基线，不能算完成正式比较。
    使用自己的处理参数/规则时，另保存中间值来核算和解释。
    """
    return None


def inside(name):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("读写路径须位于学生仓库内")
    return path


def nonempty_record(name, description):
    path = inside(name)
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        raise ValueError(f"先保存自己的{description}：{name}。结构可自由，不是统一数字规则。")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="可选新结果目录；省略时重算默认基线/主验证产物")
    parser.add_argument("--plan", default="lesson-08/report.md", help="自己的验证前计划，可放报告或独立文件")
    parser.add_argument("--split", choices=["validation", "test"], default="validation")
    parser.add_argument("--decision", help="测试前保存的自由文字选择记录")
    parser.add_argument("--selected-method", help="最后测试只评价这一自定方法名")
    args = parser.parse_args(argv)
    try:
        train, validation, audit = load_development(ROOT)
        if args.split == "test":
            if not args.output or not args.decision or not args.selected_method:
                raise ValueError("最后测试需显式新output、decision记录与selected-method；默认命令只评价验证。")
            nonempty_record(args.decision, "测试前选择")
            from mlcourse.bike_starter import load_selected_test
            evaluation = load_selected_test(ROOT, args.decision)
        else:
            if args.decision or args.selected_method:
                raise ValueError("验证不使用最后测试选择参数；先记录计划并完成验证。")
            evaluation = validation
        train_inputs = [{key: row[key] for key in INPUT_FIELDS} for row in train]
        train_targets = [row["cnt"] for row in train]
        eval_inputs = [{key: row[key] for key in INPUT_FIELDS} for row in evaluation]
        baseline_value = float(np.mean(train_targets))
        methods = {"baseline": np.full(len(evaluation), baseline_value)}
        candidate = candidate_predictions(train_inputs, train_targets, eval_inputs)
        if candidate is not None:
            nonempty_record(args.plan, "验证前计划")
            candidates = candidate if isinstance(candidate, dict) else {"candidate": candidate}
            if not candidates:
                raise ValueError("候选方法字典不能为空；无候选时返回None")
            for name, values in candidates.items():
                if not isinstance(name, str) or not name.strip() or name in methods:
                    raise ValueError("方法名须非空且不能重复；可以使用自己定义的名称")
                values = np.asarray(values, dtype=float)
                if values.shape != (len(evaluation),) or not np.all(np.isfinite(values)):
                    raise ValueError("候选须返回与评价记录等长的一列有限数值预测")
                methods[name] = values
        if args.split == "test":
            if args.selected_method not in methods:
                raise ValueError("所选方法尚未自行实现或名称不匹配，不能用另一方法冒充")
            methods = {args.selected_method: methods[args.selected_method]}
        actual = [row["cnt"] for row in evaluation]
        comparison = [{"split": args.split, "method": name, "n": len(evaluation),
                       "mae": mae(actual, predicted)} for name, predicted in methods.items()]
        records = []
        for name, predicted in methods.items():
            for row, value in zip(evaluation, predicted, strict=True):
                records.append({"datetime": row["datetime"], "split": args.split,
                                "hr": row["hr"], "workingday": row["workingday"],
                                "weathersit": row["weathersit"], "mnth": row["mnth"],
                                "cnt": row["cnt"], "method": name, "prediction": float(value),
                                "err_signed": float(value - row["cnt"]),
                                "err_absolute": float(abs(value - row["cnt"]))})
        summary = {"purpose": "开放起点：仅基线或学生自行实现的候选，不自动完成诊断与结论",
                   "starter_only": candidate is None, "task_complete": False,
                   "evaluation_split": args.split, "training_n": len(train),
                   "evaluation_n": len(evaluation), "baseline_training_mean": baseline_value,
                   "metrics": comparison, "unit": "次租借/已记录小时",
                   "data_sha256": audit["data_sha256"],
                   "source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                      for path in [Path(__file__), ROOT / "mlcourse/bike_starter.py"]}}
        output = inside(args.output) if args.output else LESSON / "artifacts/baseline"
        if args.output and output.exists():
            raise ValueError("显式结果目录已存在，换新目录以保留旧证据")
        output.mkdir(parents=True, exist_ok=not bool(args.output))
        for name, obj in [("summary.json", summary), ("data_audit.json", audit)]:
            (output / name).write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2,
                                                allow_nan=False) + "\n", encoding="utf-8")
        write_csv(output / "comparison.csv", comparison)
        write_csv(output / "records.csv", records)
        print(f"结果写入：{output.relative_to(ROOT)}")
        print(f"{args.split}: n={len(evaluation)}；训练均值基线={baseline_value:.3f} 次租借")
        print("尚无候选；请自行设计对照、核算与失败检查，再更新自己的提交清单。" if candidate is None
              else "候选来自你的实现；仍需独立核算、失败检查与建议，程序不自动判项目完成。")
        return 0
    except (OSError, ValueError, ImportError) as error:
        print(f"无法继续：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
