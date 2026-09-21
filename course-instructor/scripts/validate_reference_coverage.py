"""验证教师变体的可运行性、计算边界和确定性。

C01–S06 仍使用共享运行时，本脚本保留其独立数值核算。有
``config-support.json`` 的 S07 以后课包改用本课 ``analysis.py``：实际运行
支持变体，检查指定产物，并用第二次运行核对确定性。各课机制的
专项数值断言位于学生模板的专属测试中，本脚本不把“命令运行成功”
冒充为第二份数学证明。
"""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import numpy as np

from foundation_reference import verify as verify_foundations


ROOT = Path(__file__).resolve().parents[1]
IDS = ["C01", "C02"] + [f"S{i:02d}" for i in range(1, 31)]
SHARED_RUNTIME_IDS = {"C01", "C02", *(f"S{i:02d}" for i in range(1, 7))}
SPECIALIZED_TESTS = {
    **{f"S{i:02d}": "tests/test_s07_s12_rewrite.py" for i in range(7, 13)},
    **{f"S{i:02d}": "tests/test_pretrained_module.py" for i in range(13, 19)},
    **{f"S{i:02d}": "tests/test_workflow_module.py" for i in range(19, 25)},
    **{f"S{i:02d}": "tests/test_operations_module.py" for i in range(25, 31)},
}


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def close(actual, expected, message, tolerance=1e-7):
    if abs(actual - expected) > tolerance:
        raise AssertionError(f"{message}: {actual} != {expected}")


def lesson_number(lesson: str) -> int:
    return int(lesson[1:]) if lesson.startswith("C") else int(lesson[1:]) + 2


def independent_predictions(result, config):
    """只读取实际预测和真实结果，重新计算分母及损失。"""
    detail = result["details"]
    metrics = result["metrics"]
    checks = []
    if "actual" not in detail or "prediction" not in detail:
        return checks
    actual = np.array(detail["actual"])
    prediction = np.array(detail["prediction"])
    check(actual.shape == prediction.shape and len(actual) > 0, "预测必须一一对应")
    if "mae" in metrics:
        close(metrics["mae"], float(abs(actual - prediction).mean()), "MAE独立核算")
        close(
            metrics["rmse"],
            float(np.sqrt(((actual - prediction) ** 2).mean())),
            "RMSE独立核算",
        )
        cost = config.get("underestimate_cost", 2.0)
        loss = np.where(
            prediction < actual,
            cost * (actual - prediction),
            prediction - actual,
        )
        close(
            metrics["asymmetric_loss"],
            float(loss.mean()),
            "不对称损失独立核算",
        )
        checks.append("真实结果/预测逐条重算回归损失")
    elif "brier" in metrics:
        threshold = config.get("threshold", 0.5)
        selected = prediction >= threshold
        expected = {
            "tp": int(np.sum(selected & (actual == 1))),
            "fp": int(np.sum(selected & (actual == 0))),
            "fn": int(np.sum(~selected & (actual == 1))),
            "tn": int(np.sum(~selected & (actual == 0))),
        }
        for key, value in expected.items():
            check(metrics[key] == value, f"{key}独立核算")
        close(
            metrics["brier"],
            float(((actual - prediction) ** 2).mean()),
            "Brier独立核算",
        )
        checks.append("真实标签/概率逐条重算混淆计数和Brier")
    return checks


def shared_runtime_checks(lesson, data, config, result):
    """C01–S06 的独立核算；不用新课包的默认输出当教师答案。"""
    if lesson in {f"S{i:02d}" for i in range(1, 7)}:
        return verify_foundations(lesson, data, config, result)
    check(lesson in {"C01", "C02"}, f"{lesson}不应走共享运行时核算")
    rows = data["rows"]
    detail = result["details"]
    stress = result["stress_test"]["metrics"]
    train = [row for row in rows if row["split"] == "train"]
    check(
        set(detail["train_ids"]).isdisjoint(detail["evaluation_ids"])
        or lesson == "C01",
        "训练评价分开",
    )
    for name, coefficients in detail["model_coefficients"].items():
        if name == "linear":
            matrix = np.array([[1, row["queue_length"]] for row in train])
            target = np.array([row["wait_minutes"] for row in train])
            np.testing.assert_allclose(
                coefficients,
                np.linalg.lstsq(matrix, target, rcond=None)[0],
                atol=1e-8,
            )
        elif name == "baseline":
            close(
                coefficients[0],
                sum(row["wait_minutes"] for row in train) / len(train),
                "基线只用训练标签",
            )
        else:
            np.testing.assert_allclose(
                coefficients, [config["rule_intercept"], config["rule_slope"]]
            )
    check(stress["actual"] is None and stress["mae"] is None, "未知真实值不能评价误差")
    for group, models in detail["by_period"].items():
        selected = [row for row in detail["predictions"] if row["period"] == group]
        for name, report in models.items():
            close(
                report["mae"],
                sum(
                    abs(row[f"prediction_{name}"] - row["actual"])
                    for row in selected
                )
                / len(selected),
                "分组MAE独立核算",
            )
    return ["独立核算参数、训练评价分离、分组MAE和无标签输入"]


def snapshot(directory: Path, ignored: set[str]) -> dict[str, bytes]:
    return {
        str(path.relative_to(directory)): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.name not in ignored
    }


def run_standalone(lesson, directory, case, student_template):
    """运行两次指定变体，核对产物及确定性。

    ``timings.csv`` 只记录本机实测耗时，它必然有波动；如果课包产生它，
    我们检查文件存在且非空，但不把它纳入逐字节确定性比较。
    case 可用 ``data_file`` 显式指定非默认数据，例如 S24 独立 holdout；
    没有该字段时仍使用学生程序的默认开发数据。
    """
    config_name = case.get("config_file", "config-support.json")
    config_path = directory / config_name
    check(config_path.is_file(), f"{lesson}缺少{config_name}")
    data_name = case.get("data_file")
    data_path = directory / data_name if data_name else None
    if data_path is not None:
        check(data_path.is_file(), f"{lesson}缺少{data_name}")
    expected = case.get("expected_outputs", ["summary.json"])
    ignored = set(case.get("nondeterministic_outputs", [])) | {"timings.csv"}
    snapshots = []
    timing_seen = False
    with tempfile.TemporaryDirectory(prefix=f"reference-{lesson}-") as temporary:
        base = Path(temporary)
        for repetition in (1, 2):
            output = base / str(repetition)
            command = [
                sys.executable,
                str(directory / "analysis.py"),
                "--config",
                str(config_path),
            ]
            if data_path is not None:
                command.extend(["--data", str(data_path)])
            command.extend(["--output", str(output)])
            completed = subprocess.run(
                command,
                cwd=student_template,
                capture_output=True,
                text=True,
                timeout=60,
                env={
                    **os.environ,
                    "OPENBLAS_NUM_THREADS": "1",
                    "OMP_NUM_THREADS": "1",
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONHASHSEED": "0",
                },
            )
            check(
                completed.returncode == 0,
                f"{lesson} standalone运行失败: {completed.stderr or completed.stdout}",
            )
            for name in expected:
                path = output / name
                check(path.is_file() and path.stat().st_size > 0, f"{lesson}缺少非空产物{name}")
            summary_path = output / "summary.json"
            check(summary_path.is_file(), f"{lesson}缺少summary.json")
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            check(isinstance(summary, dict) and summary, f"{lesson} summary.json应为非空对象")
            files = [path for path in output.rglob("*") if path.is_file()]
            check(len(files) >= 2, f"{lesson}除汇总外还应有可追溯产物")
            timing = output / "timings.csv"
            if timing.exists():
                check(timing.stat().st_size > 0, f"{lesson} timings.csv不得为空")
                timing_seen = True
            snapshots.append(snapshot(output, ignored))
    check(snapshots[0] == snapshots[1], f"{lesson}相同输入的确定性产物不一致")

    checks = [
        f"实际运行{config_name}变体",
        f"核对非空产物：{', '.join(expected)}",
        "相同输入两次运行的确定性产物逐字节一致",
    ]
    if data_name:
        checks.insert(1, f"显式读取{data_name}")
    if timing_seen:
        checks.append("本机耗时表存在且非空；耗时值不作确定性断言")

    specialized = case.get("specialized_test", SPECIALIZED_TESTS.get(lesson))
    if specialized:
        path = student_template / specialized
        check(path.is_file(), f"{lesson}缺少专项测试{specialized}")
        source = path.read_text(encoding="utf-8").lower()
        check(f"test_{lesson.lower()}_" in source, f"{specialized}未显式覆盖{lesson}")
        checks.append(f"数值与机制专项断言由{specialized}覆盖")
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--student-template", type=Path, default=ROOT.parent / "course-student-template"
    )
    parser.add_argument("--lesson", choices=IDS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    student_template = args.student_template.resolve()
    sys.path.insert(0, str(student_template))
    from mlcourse.runtime import run_experiment

    started = time.perf_counter()
    reports = []
    for lesson in ([args.lesson] if args.lesson else IDS):
        directory = student_template / f"lesson-{lesson_number(lesson):02d}"
        case = json.loads((ROOT / "reference" / lesson / "case.json").read_text())
        if "lesson" in case:
            check(case["lesson"] == lesson, f"{lesson} case.json课号不一致")
        support_config = directory / "config-support.json"
        standalone = lesson not in SHARED_RUNTIME_IDS and support_config.is_file()
        if standalone:
            checks = run_standalone(lesson, directory, case, student_template)
            variant = (
                case["purpose"]
                if case.get("runner") == "standalone"
                else "config-support.json 提供的单因素变体"
            )
            metrics = None
            runner = "standalone_analysis"
        else:
            check(lesson in SHARED_RUNTIME_IDS, f"{lesson}既无独立支持配置，也不属于共享运行时课次")
            data = json.loads((directory / "data/base.json").read_text())
            config = json.loads((directory / "config.json").read_text())
            config.update(case["config_patch"])
            if case.get("duplicate_first_row"):
                data["rows"].append(copy.deepcopy(data["rows"][0]))
            result = run_experiment(lesson, data, config)
            checks = independent_predictions(result, config) + shared_runtime_checks(
                lesson, data, config, result
            )
            check(bool(checks), "没有独立检查")
            variant = case["purpose"]
            metrics = result["metrics"]
            runner = "shared_runtime_with_independent_recalculation"
        reports.append(
            {
                "lesson": lesson,
                "runner": runner,
                "variant": variant,
                "checks": checks,
                "metrics": metrics,
            }
        )
    report = {
        "status": "passed",
        "lessons": len(reports),
        "independent_checks": sum(len(row["checks"]) for row in reports),
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "scope": (
            "C01–S06独立重算数值；新standalone课包实际运行支持变体并核对"
            "产物与确定性。standalone课次的专项数学和机制断言由报告中列出的"
            "学生模板测试覆盖；本报告不评价学生选择、结论或真人可读性"
        ),
        "results": reports,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
