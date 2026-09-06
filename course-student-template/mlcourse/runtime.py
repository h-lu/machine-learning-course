"""命令行入口与结果追溯；不替学生填写结论。"""

from __future__ import annotations
import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
import numpy as np
from .experiments import EXPERIMENTS


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
        for name in ("runtime.py", "mathops.py", "experiments.py")
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


def main(lesson_directory):
    parser = argparse.ArgumentParser(
        description="运行本课小实验；结果只作为入门示例，学生自行论证采用方案。"
    )
    parser.add_argument("--config", type=Path, default=lesson_directory / "config.json")
    parser.add_argument(
        "--data", type=Path, default=lesson_directory / "data/base.json"
    )
    parser.add_argument("--output", type=Path, default=lesson_directory / "artifacts")
    args = parser.parse_args()
    try:
        data = json.loads(args.data.read_text(encoding="utf-8"))
        config = json.loads(args.config.read_text(encoding="utf-8"))
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
        print(f"{lesson_directory.name}: 示例实验已运行，结果写入 {path}")
    except (ValueError, KeyError, TypeError, IndexError, OSError) as error:
        parser.exit(
            2,
            f"无法运行：{error}\n请检查数据说明、字段和参数。起步实验运行失败时，先使用原始小数据定位问题。\n",
        )
