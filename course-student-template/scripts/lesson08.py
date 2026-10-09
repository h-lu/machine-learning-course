"""第 8 课：短热身、生成待填事前实验计划、验证比较、保存决策后最后评价。"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="task", required=True)
    warmup = commands.add_parser("warmup", help="短追踪：旧人工样本的训练均值填补与给定规则")
    warmup.add_argument("--output", required=True, help="新的结果目录；不覆盖已有结果")
    prereg = commands.add_parser("preregister", help="生成待填写事前实验计划；不会运行模型或给出解释")
    prereg.add_argument("--config", default="lesson-08/config-hour-onehot.json")
    prereg.add_argument("--output", required=True, help="新的 JSON 文件，例如 lesson-08/preregister.json")
    decision = commands.add_parser("decision", help="从已保存的验证运行生成待填写决策")
    decision.add_argument("--validation-run", required=True)
    decision.add_argument("--output", required=True, help="新的 JSON 文件，例如 lesson-08/decision.json")
    bike = commands.add_parser("bike", help="运行真实逐小时数据上的一个单因素比较")
    bike.add_argument("--config", default="lesson-08/config-hour-onehot.json")
    bike.add_argument("--preregister", help="验证前已经填写并独立保存的事前实验计划 JSON")
    bike.add_argument("--output", help="新结果目录；显式路径不覆盖。省略时重算默认 lesson-08/artifacts/run")
    bike.add_argument("--unlock-test", action="store_true", help="明确打开最后测试，只评价事先选择的方法")
    bike.add_argument("--decision", help="引用已保存验证运行的决策 JSON")
    bike.add_argument("--allow-fixture", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        from bike_runtime import (config_from, decision_draft, preregister_draft,
                                  run_bike, run_warmup, safe_path, write_new_json)
        replace_default = args.task == "bike" and args.output is None
        output = safe_path(ROOT, args.output or "lesson-08/artifacts/run")
        if output.exists() and not replace_default:
            raise ValueError("输出路径已经存在；请使用新 --output，保留以前的比较证据")
        if args.task == "warmup":
            run_warmup(ROOT, output)
        elif args.task == "preregister":
            config = config_from(safe_path(ROOT, args.config))
            write_new_json(output, preregister_draft(config))
            print(f"待填事前实验计划：{output.relative_to(ROOT)}。先填写指标、解释和检查规则，再运行验证。")
        elif args.task == "decision":
            write_new_json(output, decision_draft(ROOT, safe_path(ROOT, args.validation_run)))
            print(f"待填决策：{output.relative_to(ROOT)}。先选 original/candidate 并说明验证依据。")
        else:
            run_bike(ROOT, safe_path(ROOT, args.config), output,
                     preregister_path=safe_path(ROOT, args.preregister) if args.preregister else None,
                     unlock_test=args.unlock_test,
                     decision_path=safe_path(ROOT, args.decision) if args.decision else None,
                     allow_fixture=args.allow_fixture, replace_default=replace_default)
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"无法继续：{error}\n请核对 ENVIRONMENT.md 的目录、数据和命令；不要手改结果文件。", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
