"""运行32个教师变体，并独立核对数值；检查工具示例，不规定学生答案。"""

from __future__ import annotations
import argparse
import copy
import json
import sys
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
IDS = ["C01", "C02"] + [f"S{i:02d}" for i in range(1, 31)]


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def close(actual, expected, message, tolerance=1e-7):
    if abs(actual - expected) > tolerance:
        raise AssertionError(f"{message}: {actual} != {expected}")


def independent_predictions(result, config):
    """只读取实际预测和真实结果，重新计算分母及损失。"""
    detail = result["details"]
    metrics = result["metrics"]
    checks = []
    if "actual" not in detail or "prediction" not in detail:
        return checks
    y = np.array(detail["actual"])
    p = np.array(detail["prediction"])
    check(y.shape == p.shape and len(y) > 0, "预测必须一一对应")
    if "mae" in metrics:
        close(metrics["mae"], float(abs(y - p).mean()), "MAE独立核算")
        close(metrics["rmse"], float(np.sqrt(((y - p) ** 2).mean())), "RMSE独立核算")
        cost = config.get("underestimate_cost", 2.0)
        loss = np.where(p < y, cost * (y - p), p - y)
        close(metrics["asymmetric_loss"], float(loss.mean()), "不对称损失独立核算")
        checks.append("真实结果/预测逐条重算回归损失")
    elif "brier" in metrics:
        threshold = config.get("threshold", 0.5)
        prediction = p >= threshold
        expected = {
            "tp": int(np.sum(prediction & (y == 1))),
            "fp": int(np.sum(prediction & (y == 0))),
            "fn": int(np.sum(~prediction & (y == 1))),
            "tn": int(np.sum(~prediction & (y == 0))),
        }
        for key, value in expected.items():
            check(metrics[key] == value, f"{key}独立核算")
        close(metrics["brier"], float(((y - p) ** 2).mean()), "Brier独立核算")
        checks.append("真实标签/概率逐条重算混淆计数和Brier")
    return checks


def specific_checks(lesson, data, config, result):
    m = result["metrics"]
    detail = result["details"]
    stress = result["stress_test"]["metrics"]
    checks = []
    rows = data.get("rows", [])
    if lesson in {"C01", "C02"}:
        train = [r for r in rows if r["split"] == "train"]
        check(set(detail["train_ids"]).isdisjoint(detail["evaluation_ids"]) or lesson == "C01", "训练评价分开")
        for name, coefficients in detail["model_coefficients"].items():
            if name == "linear":
                x = np.array([[1, r["queue_length"]] for r in train])
                y = np.array([r["wait_minutes"] for r in train])
                np.testing.assert_allclose(coefficients, np.linalg.lstsq(x, y, rcond=None)[0], atol=1e-8)
            elif name == "baseline":
                close(coefficients[0], sum(r["wait_minutes"] for r in train) / len(train), "基线只用训练标签")
            else:
                np.testing.assert_allclose(coefficients, [config["rule_intercept"], config["rule_slope"]])
        check(stress["actual"] is None and stress["mae"] is None, "未知真实值不能评价误差")
        for group, models in detail["by_period"].items():
            selected = [r for r in detail["predictions"] if r["period"] == group]
            for name, report in models.items():
                close(report["mae"], sum(abs(r[f"prediction_{name}"] - r["actual"]) for r in selected) / len(selected), "分组MAE独立核算")
        checks += ["独立核算参数、训练评价分离、分组MAE和无标签输入"]
    elif lesson == "S01":
        close(m["cost"], m["fp"] + config["false_negative_cost"] * m["fn"], "代价")
        checks += ["替换错误代价后独立计算总损失"]
    elif lesson == "S02":
        visible = [r for r in rows if r["available_day"] <= config["observation_day"]]
        check(m["visible_labels"] == len(visible), "观察截止日期计数")
        close(
            m["annotator_agreement"],
            sum(r["label"] == r["annotator_b"] for r in rows) / len(rows),
            "标注一致率",
        )
        checks += ["直接扫描记录核对观察截止日期与标注一致率"]
    elif lesson == "S03":
        train = set(detail["group"]["train_ids"])
        evaluation = set(detail["group"]["evaluation_ids"])
        check(not train & evaluation, "训练评估行重复")
        check(m["shared_users"] == 0, "分组后用户泄漏")
        check(stress["mae"] < 1e-6, "事后标签特征应暴露虚假高分")
        checks += ["分组切分用户不重叠，事后标签特征泄漏被数值展示"]
    elif lesson == "S04":
        check(stress["rmse"] > m["rmse"], "极端结果未改变RMSE")
        checks += ["独立极端结果导致尾部误差增加"]
    elif lesson == "S05":
        p = np.array(detail["prediction"])
        indices = np.argsort(-p, kind="stable")[: config["capacity"]]
        check(detail["selected_indices"] == indices.tolist(), "名额排序")
        check(sum(b["n"] for b in detail["calibration"]) == len(p), "分箱分母")
        checks += ["独立排序核对名额及分箱计数守恒"]
    elif lesson == "S06":
        x = np.array(
            [
                [r["x1"], np.nan if r["x2"] is None else r["x2"]]
                for r in rows
                if r["split"] == "train"
            ]
        )
        expected = np.nanmean(x, axis=0)
        np.testing.assert_allclose(detail["training_fill"], expected, atol=1e-8)
        checks += ["仅从训练行重算缺失填补值"]
    elif lesson == "S07":
        train = [r for r in rows if r["split"] == "train"]
        a = np.array([[1, r["x1"], r["x2"]] for r in train])
        y = np.array([r["target"] for r in train])
        penalty = np.diag([0, config["ridge"], config["ridge"]])
        w = np.linalg.solve(a.T @ a + penalty, a.T @ y)
        np.testing.assert_allclose(detail["coefficients"], w, atol=1e-8)
        checks += ["独立解正规方程核对ridge系数"]
    elif lesson == "S08":
        check(len(detail["train_curve"]) > 2, "缺少训练轨迹")
        check(
            all(np.isfinite(item["loss"]) for item in detail["train_curve"]),
            "损失非有限",
        )
        checks += ["概率模型真实优化轨迹与有限损失"]
    elif lesson == "S09":

        def leaves(tree, depth=0):
            if "feature" not in tree:
                return [(depth, tree["n"])]
            return leaves(tree["left"], depth + 1) + leaves(tree["right"], depth + 1)

        leaf = leaves(detail["tree"])
        check(max(depth for depth, _ in leaf) <= config["max_depth"], "树超过设定深度")
        check(
            sum(n for _, n in leaf) == sum(r["split"] == "train" for r in rows),
            "叶计数",
        )
        checks += ["独立遍历树核对深度与训练行守恒"]
    elif lesson == "S10":
        check(
            detail["model_tree_counts"]["bagging"] == config["n_estimators"], "集成数"
        )
        check(
            detail["operations_proxy"]["bagging"]
            == detail["operations_proxy"]["single"] * config["n_estimators"],
            "操作数估算",
        )
        checks += ["不同集成规模的实际模型数量与操作数估算"]
    elif lesson == "S11":
        labels = np.array(detail["assignments"])
        centres = np.array(detail["centres"])
        x = np.array([[r["x1"], r["x2"]] for r in rows])
        if config["standardize"]:
            x = (x - x.mean(axis=0)) / x.std(axis=0)
        close(
            m["inertia"], float(((x - centres[labels]) ** 2).sum()), "簇内平方和", 1e-6
        )
        checks += ["从原始数据和最终中心独立计算簇内平方和"]
    elif lesson == "S12":
        basis = np.array(detail["basis"])
        np.testing.assert_allclose(
            basis @ basis.T, np.eye(config["components"]), atol=1e-8
        )
        check(
            len(detail["reconstruction_errors"])
            == sum(r["split"] != "train" for r in rows),
            "重构分母",
        )
        checks += ["主成分正交性与重构记录数量"]
    elif lesson in {"S13", "S14"}:
        curve = detail["train_curve"]
        check(all("validation_log_loss" in point for point in curve), "缺验证曲线")
        close(curve[-1]["validation_log_loss"], m["log_loss"], "最终验证损失与预测对应")
        checks += ["训练/验证两条曲线与最终预测相符"]
    elif lesson == "S15":
        images = np.array([r["pixels"] for r in rows])
        kernel = np.array([[-1, 2, -1], [-1, 2, -1], [-1, 2, -1]])
        expected = float(np.sum(images[0, :3, :3] * kernel))
        close(detail["first_feature_maps"][0][0][0], expected, "首个卷积窗口")
        checks += ["手工点乘一个卷积窗口核对真实卷积运算"]
    elif lesson == "S16":
        check(len(detail["training_ids"]) == config["training_examples"], "小样本数量")
        check(detail["no_finetuning_performed"] is True, "不能声称真实微调")
        checks += ["替换表示路线后的训练样本数量与能力声明"]
    elif lesson == "S17":
        weights = np.array(detail["attention_weights"])
        np.testing.assert_allclose(weights.sum(axis=1), 1, atol=1e-8)
        x = np.array(data["vectors"])
        expected = x @ x.T / np.sqrt(x.shape[1]) / config["temperature"]
        expected = np.exp(expected - expected.max(axis=1, keepdims=True))
        expected /= expected.sum(axis=1, keepdims=True)
        np.testing.assert_allclose(weights, expected, atol=1e-8)
        checks += ["独立计算无遮罩softmax注意力全部权重"]
    elif lesson == "S18":
        before = np.array(detail["probabilities_before"])
        after = np.array(detail["probabilities_after"])
        targets = np.array(detail["targets"])
        close(
            m["next_token_loss_before"],
            float(-np.log(before[np.arange(len(targets)), targets]).mean()),
            "交叉熵",
        )
        check(
            m["next_token_loss_after"] < m["next_token_loss_before"], "小步输出头更新"
        )
        check(stress["first_position_change_l2"] > 0, "关掉遮罩应看到未来扰动")
        checks += ["独立交叉熵及关闭遮罩后的未来信息效应"]
    elif lesson == "S19":
        close(m["perplexity"], float(np.exp(m["next_token_log_loss"])), "困惑度")
        check(m["unknown_tokens"] == 1, "未知字符计数")
        checks += ["已知词表外字符与困惑度指数关系"]
    elif lesson == "S20":
        distribution = np.array(detail["distribution_after_start"])
        close(float(distribution.sum()), 1, "抽样归一化")
        check(int((distribution > 0).sum()) <= config["top_k"], "top-k支持集")
        check(
            len(detail["sample_ids"]) == config["samples"],
            "必须保存全部采样序列以重算统计量",
        )
        checks += ["改变解码配置后的概率支持集和归一化"]
    elif lesson == "S21":
        cases = detail["evaluation_cases"]
        correct = sum(r["response"] == r["expected"] for r in cases)
        check(m["correct"] == correct, "人工响应表逐条正确数")
        check(not detail["unseen_prompt_evaluated"], "不能声称执行未缓存提示")
        checks += ["逐条重新计数候选响应，不替未执行提示编造结果"]
    elif lesson == "S22":
        check(
            all(len(row["retrieved"]) <= config["top_k"] for row in detail["queries"]),
            "检索返回数",
        )
        check(m["query_count"] == len(data["queries"]), "查询数量")
        checks += ["候选文档数量及查询分母"]
    elif lesson == "S23":
        documents = {r["id"]: r for r in data["documents"]}
        for case in detail["cases"]:
            if case["citation"]:
                check(
                    case["answer"] == documents[case["citation"]]["text"],
                    "引用正文不一致",
                )
        check(m["correct"] == sum(r["correct"] for r in detail["cases"]), "回答正确数")
        checks += ["逐条引用必须对应原始文档正文"]
    elif lesson == "S24":
        cases = detail["decisions"]
        check(
            m["unsafe_actions_allowed"]
            == sum(r["accepted"] and not r["expected_allowed"] for r in cases),
            "不允许动作计数",
        )
        check(
            m["safe_requests_blocked"]
            == sum(not r["accepted"] and r["expected_allowed"] for r in cases),
            "误拒计数",
        )
        checks += ["直接重算危险动作通过与正常请求误拒"]
    elif lesson == "S25":
        close(sum(m["mean_action_counts"]), config["steps"], "动作次数", 1e-6)
        check(0 <= m["mean_reward"] <= config["steps"], "累计奖励范围")
        check(m["mean_pseudo_regret"] >= 0, "遗憾不能负")
        checks += ["仿真动作数量守恒与回报范围"]
    elif lesson == "S26":
        trajectory = detail["trajectory"]
        total = sum(
            config["gamma"] ** i * row["reward"] for i, row in enumerate(trajectory)
        )
        close(m["discounted_return"], total, "轨迹折扣回报")
        checks += ["从轨迹奖励独立求折扣回报"]
    elif lesson == "S27":
        values = detail["values"]
        width = data["width"]
        gamma = config["gamma"]
        residual = 0.0
        for state, value in enumerate(values):
            if state == data["goal"] or state in data["hazards"]:
                close(value, 0, "终止状态价值")
                continue
            q = []
            row, column = divmod(state, width)
            for dr, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
                r, col = row + dr, column + dc
                nxt = (
                    r * width + col
                    if 0 <= r < data["height"] and 0 <= col < width
                    else state
                )
                terminal = nxt == data["goal"] or nxt in data["hazards"]
                reward = (
                    data["goal_reward"]
                    if nxt == data["goal"]
                    else (
                        data["hazard_reward"]
                        if nxt in data["hazards"]
                        else data["step_reward"]
                    )
                )
                q.append(reward + (0 if terminal else gamma * values[nxt]))
            residual = max(residual, abs(value - max(q)))
        check(residual < config["tolerance"] * 2 + 1e-8, "独立Bellman残差")
        checks += ["独立实现环境转移计算全部状态Bellman残差"]
    elif lesson == "S28":
        check(
            set(detail["training_seeds"]).isdisjoint(detail["evaluation_seeds"]),
            "训练和评估种子未分开",
        )
        check(len(detail["per_evaluation"]) == 25, "五乘五评估次数")
        close(
            m["goal_rate"],
            sum(row["goal_reached"] for row in detail["per_evaluation"]) / 25,
            "目标到达率",
        )
        check(
            all(
                row["initial_state"] != data["start"]
                for row in detail["per_evaluation"]
            ),
            "未改变起点",
        )
        checks += ["冻结策略在独立种子选择的新起点评估，逐次重算成功率"]
    elif lesson == "S29":
        check(
            result["comparison"]["input_check"]["missing_x2_rejected"], "缺字段未拒绝"
        )
        check(detail["adoption_decision"] is None, "程序不替学生决定上线")
        checks += ["缺输入字段拒绝与不预填上线结论"]
    elif lesson == "S30":
        comparison = result["comparison"]
        check(
            comparison["old_on_adaptation_holdout"]["n"]
            == comparison["adapted_on_first_half_of_new_batch"]["n"],
            "迁移比较分母不同",
        )
        check(
            detail["adaptation_training_rows"] + detail["adaptation_evaluation_rows"]
            == len(detail["transfer_actual"]),
            "新数据切分",
        )
        checks += ["原模型与更新模型在同一批保留数据比较"]
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--student-template", type=Path, default=ROOT.parent / "course-student-template"
    )
    parser.add_argument("--lesson", choices=IDS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.student_template.resolve()))
    from mlcourse.runtime import run_experiment

    started = time.perf_counter()
    reports = []
    for lesson in ([args.lesson] if args.lesson else IDS):
        number = int(lesson[1:]) if lesson.startswith("C") else int(lesson[1:]) + 2
        directory = args.student_template / f"lesson-{number:02d}"
        data = json.loads((directory / "data/base.json").read_text())
        config = json.loads((directory / "config.json").read_text())
        case = json.loads((ROOT / "reference" / lesson / "case.json").read_text())
        config.update(case["config_patch"])
        if case.get("duplicate_first_row"):
            data["rows"].append(copy.deepcopy(data["rows"][0]))
        result = run_experiment(lesson, data, config)
        checks = independent_predictions(result, config) + specific_checks(
            lesson, data, config, result
        )
        check(bool(checks), "没有独立检查")
        reports.append(
            {
                "lesson": lesson,
                "variant": case["purpose"],
                "checks": checks,
                "metrics": result["metrics"],
            }
        )
    report = {
        "status": "passed",
        "lessons": len(reports),
        "independent_checks": sum(len(r["checks"]) for r in reports),
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "scope": "验证32个工具变体及数值性质，不评价学生是否选择相同模型或采用结论",
        "results": reports,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
