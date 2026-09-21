"""S25–S30：同一服务台作品从反馈、运行到迁移和交付的离线实验。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


LESSON_BY_NUMBER = {27: "S25", 28: "S26", 29: "S27", 30: "S28", 31: "S29", 32: "S30"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _validate(data: dict[str, Any], lesson: str) -> None:
    _require(data.get("kind") == "campus_service_lifecycle", "数据 kind 应为 campus_service_lifecycle")
    _require(data.get("project_id") == "equipment-helpdesk-v1", "六课必须追踪同一 project_id")
    required = {
        "S25": "feedback_rounds",
        "S26": "decision_cases",
        "S27": "monitoring_records",
        "S28": "performance_requests",
        "S29": "transfer_requests",
        "S30": "transfer_requests",
    }
    if lesson == "S30":
        has_development = isinstance(data.get("transfer_requests"), list) and bool(data["transfer_requests"])
        has_final = isinstance(data.get("delivery_requests"), list) and bool(data["delivery_requests"])
        _require(has_development or has_final, "缺少 transfer_requests 或 delivery_requests")
    else:
        _require(isinstance(data.get(required[lesson]), list) and data[required[lesson]], f"缺少 {required[lesson]}")


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _run_bandit(rows: list[dict], policy: str, epsilon: float, seed: int) -> tuple[dict, list[dict]]:
    rng = random.Random(seed)
    order = list(rows)
    rng.shuffle(order)
    counts = Counter({"brief": 0, "guided": 0})
    totals = Counter({"brief": 0.0, "guided": 0.0})
    records = []
    cumulative = 0.0
    for index, row in enumerate(order, 1):
        estimates = {
            action: (totals[action] / counts[action] if counts[action] else 0.0)
            for action in ("brief", "guided")
        }
        explore = policy == "epsilon" and rng.random() < epsilon
        if explore:
            action = rng.choice(["brief", "guided"])
        else:
            action = max(("brief", "guided"), key=lambda item: (estimates[item], item == "brief"))
        reward = int(row[f"{action}_feedback"])
        counts[action] += 1
        totals[action] += reward
        cumulative += reward
        records.append({
            "seed": seed,
            "round": index,
            "request_id": row["id"],
            "request_type": row["request_type"],
            "policy": policy,
            "epsilon": epsilon,
            "chosen_response": action,
            "observed_feedback": reward,
            "other_response_feedback": "未观察",
            "exploration_step": explore,
            "cumulative_feedback": cumulative,
        })
    return {
        "mean_feedback": cumulative / len(order),
        "observed_feedback": int(cumulative),
        "rounds": len(order),
        "response_types_tried": sum(counts[action] > 0 for action in counts),
        "action_counts": dict(counts),
    }, records


def run_s25(data: dict, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    rows = data["feedback_rounds"]
    seeds = config["seeds"]
    _require(isinstance(seeds, list) and len(seeds) >= 3, "至少需要三个随机种子")
    all_records, episode_rows = [], []
    for policy, epsilon in (("greedy", 0.0), ("epsilon", float(config["exploration_rate"]))):
        for seed in seeds:
            summary, records = _run_bandit(rows, policy, epsilon, int(seed))
            all_records.extend(records)
            episode_rows.append({"policy": policy, "seed": seed, **summary})
    comparison = {}
    for policy in ("greedy", "epsilon"):
        selected = [row for row in episode_rows if row["policy"] == policy]
        comparison[policy] = {
            "episodes": len(selected),
            "mean_feedback_per_round": _mean([row["mean_feedback"] for row in selected]),
            "mean_response_types_tried": _mean([row["response_types_tried"] for row in selected]),
            "mean_brief_count": _mean([row["action_counts"]["brief"] for row in selected]),
            "mean_guided_count": _mean([row["action_counts"]["guided"] for row in selected]),
        }
    result = {
        "lesson": "S25",
        "project_id": data["project_id"],
        "comparison": comparison,
        "denominator": {"rounds_per_episode": len(rows), "episodes_per_policy": len(seeds)},
        "feedback_boundary": "程序只把被选回答的反馈交给策略；另一回答的结果在当轮未观察。",
        "evidence_type": "课程编写者制作的离线反馈模拟，不是真实使用者实验。",
    }
    return result, {"rounds": all_records, "episodes": episode_rows}


def _decision_action(policy: str, visible_state: dict[str, str]) -> str:
    if policy == "fast_auto":
        return "auto_answer"
    risk = visible_state.get("risk")
    return "human_review" if risk != "low" else "auto_answer"


def run_s26(data: dict, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    fields = config["state_fields"]
    _require(isinstance(fields, list) and fields, "state_fields 不能为空")
    records = []
    totals: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in data["decision_cases"]:
        visible = {field: row[field] for field in fields if field in row}
        for policy in ("fast_auto", "risk_aware"):
            action = _decision_action(policy, visible)
            immediate = 1.0 if action == "auto_answer" else 1.0 - float(config["human_delay_cost"])
            if action == "auto_answer":
                outcome = 1.0 if row["auto_resolved"] else -1.0
                delayed = -float(config["delayed_harm_weight"]) if row["delayed_harm"] else 0.0
            else:
                outcome, delayed = 1.0, 0.0
            aligned = outcome + delayed - (float(config["human_delay_cost"]) if action == "human_review" else 0.0)
            totals["speed_score"][policy] += immediate
            totals["long_term_score"][policy] += aligned
            records.append({
                "id": row["id"],
                "visible_state": json.dumps(visible, ensure_ascii=False, sort_keys=True),
                "actual_risk": row["risk"],
                "policy": policy,
                "action": action,
                "immediate_score": immediate,
                "delayed_harm": bool(row["delayed_harm"] and action == "auto_answer"),
                "long_term_score": aligned,
            })
    comparison = {}
    for name in ("speed_score", "long_term_score"):
        scores = dict(totals[name])
        comparison[name] = {
            "scores": scores,
            "selected_policy": max(scores, key=scores.get),
            "denominator": len(data["decision_cases"]),
        }
    result = {
        "lesson": "S26",
        "project_id": data["project_id"],
        "state_fields": fields,
        "comparison": comparison,
        "delayed_harm_weight": config["delayed_harm_weight"],
        "evidence_type": "表格环境中的确定性模拟；分数来自明确规则，不代表真实使用者价值。",
    }
    return result, {"trajectories": records}


def _route_distribution(rows: list[dict], version: str) -> dict[str, float]:
    counts = Counter(row["predictions"][version]["route"] for row in rows)
    return {route: counts[route] / len(rows) for route in ("retrieve", "inventory", "calculator", "human")}


def _total_variation(a: dict[str, float], b: dict[str, float]) -> float:
    return sum(abs(a[key] - b[key]) for key in a) / 2


def _monitor_metrics(rows: list[dict], version: str, confidence_threshold: float) -> dict:
    labeled = [row for row in rows if row.get("label_available")]
    correct = sum(row["predictions"][version]["route"] == row["expected_route"] for row in labeled)
    return {
        "n": len(rows),
        "low_confidence": sum(row["predictions"][version]["confidence"] < confidence_threshold for row in rows),
        "low_confidence_rate": sum(row["predictions"][version]["confidence"] < confidence_threshold for row in rows) / len(rows),
        "new_condition": sum(bool(row["new_condition"]) for row in rows),
        "new_condition_rate": sum(bool(row["new_condition"]) for row in rows) / len(rows),
        "labeled_n": len(labeled),
        "known_correct": correct,
        "known_accuracy": correct / len(labeled) if labeled else None,
        "unlabeled_n": len(rows) - len(labeled),
    }


def run_s27(data: dict, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    version = config["candidate_version"]
    recovery = config["recovery_version"]
    rows = data["monitoring_records"]
    reference = [row for row in rows if row["batch"] == "reference"]
    current = [row for row in rows if row["batch"] == "current"]
    ref_metrics = _monitor_metrics(reference, version, config["confidence_threshold"])
    cur_metrics = _monitor_metrics(current, version, config["confidence_threshold"])
    shift = _total_variation(_route_distribution(reference, version), _route_distribution(current, version))
    early_alarm = (
        cur_metrics["low_confidence_rate"] - ref_metrics["low_confidence_rate"] > config["low_confidence_increase_limit"]
        or cur_metrics["new_condition_rate"] > config["new_condition_rate_limit"]
        or shift > config["route_shift_limit"]
    )
    label_alarm = (
        cur_metrics["known_accuracy"] is not None
        and cur_metrics["known_accuracy"] < config["known_accuracy_minimum"]
    )
    recovered = _monitor_metrics(current, recovery, config["confidence_threshold"])
    records = []
    for row in rows:
        prediction = row["predictions"][version]
        records.append({
            "id": row["id"], "batch": row["batch"], "text": row["text"],
            "model_version": version, "predicted_route": prediction["route"],
            "confidence": prediction["confidence"], "new_condition": row["new_condition"],
            "label_available": row["label_available"],
            "expected_route": row["expected_route"] if row["label_available"] else "等待标注",
            "known_correct": (prediction["route"] == row["expected_route"]) if row["label_available"] else "尚不能判断",
        })
    result = {
        "lesson": "S27",
        "project_id": data["project_id"],
        "model_versions": {"candidate": version, "recovery": recovery},
        "batches": {"reference": ref_metrics, "current": cur_metrics},
        "route_distribution_shift": shift,
        "alarms": {"before_labels": early_alarm, "after_available_labels": label_alarm},
        "recovery_check": recovered,
        "recovery_action": "切回已保存版本并把低置信请求交给人工" if early_alarm or label_alarm else "继续监测",
        "label_boundary": f"当前批次有 {cur_metrics['unlabeled_n']} 条标签尚未到达，不能计算它们的正确率。",
        "evidence_type": "监测课程提供的固定预测日志；没有重新训练模型。",
    }
    metric_rows = [
        {"stage": "candidate_reference", "version": version, **ref_metrics},
        {"stage": "candidate_current", "version": version, **cur_metrics},
        {"stage": "recovery_current", "version": recovery, **recovered},
    ]
    return result, {"monitoring_records": records, "batch_metrics": metric_rows}


def _normalise(text: str) -> str:
    return "".join(text.lower().split())


def _predict_service_route(text: str, profile: str) -> str:
    if any(word in text for word in ("密码", "账户", "导出", "修改", "预约")):
        return "human"
    if any(word in text for word in ("库存", "相机", "三脚架", "投影仪", "还有")):
        return "inventory"
    if any(word in text for word in ("费用", "多少钱", "逾期")):
        return "calculator"
    retrieve_words = ["借", "期限", "多久", "几天", "规则"]
    if profile == "thorough":
        retrieve_words += ["延长", "续借", "归还", "可借"]
    if any(word in text for word in retrieve_words):
        return "retrieve"
    return "human"


def _measured_compute(text: str, profile: str, iterations: int) -> tuple[str, float]:
    started = time.perf_counter_ns()
    digest = text.encode("utf-8")
    for _ in range(iterations):
        digest = hashlib.sha256(digest).digest()
    route = _predict_service_route(text, profile)
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    return route, elapsed_ms


def _performance_once(rows: list[dict], profile: str, cache_enabled: bool, iterations: int) -> tuple[dict, list[dict]]:
    cache: dict[tuple[str, str], str] = {}
    records, fresh_ms, lookup_ms = [], 0.0, 0.0
    hits = 0
    run_started = time.perf_counter_ns()
    for row in rows:
        key = (profile, _normalise(row["text"]))
        lookup_start = time.perf_counter_ns()
        cached = cache_enabled and key in cache
        lookup_ms += (time.perf_counter_ns() - lookup_start) / 1_000_000
        if cached:
            route = cache[key]
            hits += 1
        else:
            route, elapsed = _measured_compute(row["text"], profile, iterations)
            fresh_ms += elapsed
            if cache_enabled:
                cache[key] = route
        records.append({
            "id": row["id"], "profile": profile, "cache_enabled": cache_enabled,
            "cache_hit": cached, "predicted_route": route,
            "expected_route": row["expected_route"], "correct": route == row["expected_route"],
        })
    total_elapsed_ms = (time.perf_counter_ns() - run_started) / 1_000_000
    return {
        "profile": profile,
        "cache_enabled": cache_enabled,
        "n": len(rows),
        "correct": sum(row["correct"] for row in records),
        "cache_hits": hits,
        "fresh_calls": len(rows) - hits,
        "fresh_compute_ms": fresh_ms,
        "cache_lookup_ms": lookup_ms,
        "total_elapsed_ms": total_elapsed_ms,
        "mean_request_latency_ms": total_elapsed_ms / len(rows),
    }, records


def run_s28(data: dict, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    rows = data["performance_requests"]
    repeats = int(config["timing_repeats"])
    _require(repeats >= 3, "timing_repeats 至少为 3")
    measurement_rows, first_records = [], []
    deterministic = []
    for profile in ("fast", "thorough"):
        iterations = int(config["work_iterations"][profile])
        for cache_enabled in (False, True):
            for repeat in range(1, repeats + 1):
                measured, records = _performance_once(rows, profile, cache_enabled, iterations)
                measurement_rows.append({"repeat": repeat, **measured})
                if repeat == 1:
                    first_records.extend(records)
            base = measurement_rows[-repeats]
            cost_per_call = float(config["estimated_cost_per_fresh_call"][profile])
            deterministic.append({
                "profile": profile, "cache_enabled": cache_enabled,
                "n": base["n"], "correct": base["correct"], "cache_hits": base["cache_hits"],
                "fresh_calls": base["fresh_calls"],
                "estimated_cost_units": base["fresh_calls"] * cost_per_call,
            })
    result = {
        "lesson": "S28",
        "project_id": data["project_id"],
        "deterministic_comparison": deterministic,
        "timing_file": "timings.csv",
        "timing_note": "timings.csv 是本机实际测得的请求处理耗时；total_elapsed_ms 是一批 10 条的总时间，mean_request_latency_ms 是总时间除以 10。每次运行会波动，它不是模型推理耗时。",
        "cost_note": "estimated_cost_units 来自配置中的估算单价，不是账单或实测金额。",
        "cache_note": "缓存键同时包含输入文字和方案名称；命中只表示重放相同结果。",
    }
    tables = {"records": first_records, "timings": measurement_rows}
    check = config.get("repeat_input_check")
    if check is not None:
        _require(isinstance(check, dict), "repeat_input_check 应为对象")
        request_id = check.get("id")
        replacement = check.get("replacement_text")
        _require(isinstance(replacement, str) and replacement.strip(), "replacement_text 不能为空")
        _require(request_id in {"P05", "P08"}, "repeat_input_check.id 只能为 P05 或 P08")
        changed_rows = [dict(row) for row in rows]
        targets = [row for row in changed_rows if row["id"] == request_id]
        _require(len(targets) == 1, "repeat_input_check.id 必须对应唯一请求")
        target = targets[0]
        original_text = target["text"]
        _require(_normalise(replacement) != _normalise(original_text), "替换文字必须与该行原文不同")
        _require(
            _normalise(replacement) not in {_normalise(row["text"]) for row in changed_rows if row["id"] != request_id},
            "替换文字不能与其他请求相同，否则仍是缓存重复",
        )
        target["text"] = replacement
        changed_comparison, changed_records = [], []
        for profile in ("fast", "thorough"):
            iterations = int(config["work_iterations"][profile])
            for cache_enabled in (False, True):
                measured, records = _performance_once(changed_rows, profile, cache_enabled, iterations)
                changed_records.extend(records)
                cost_per_call = float(config["estimated_cost_per_fresh_call"][profile])
                changed_comparison.append({
                    "profile": profile,
                    "cache_enabled": cache_enabled,
                    "n": measured["n"],
                    "correct": measured["correct"],
                    "cache_hits": measured["cache_hits"],
                    "fresh_calls": measured["fresh_calls"],
                    "estimated_cost_units": measured["fresh_calls"] * cost_per_call,
                })
        result["repeat_input_check"] = {
            "id": request_id,
            "original_text": original_text,
            "replacement_text": replacement,
            "comparison_after_change": changed_comparison,
        }
        tables["changed_records"] = changed_records
    return result, tables


def _transfer_route(text: str, scheme: str) -> str:
    if any(word in text for word in ("密码", "账户", "导出", "修改", "预约", "个人信息", "读者信息")):
        return "human"
    inventory = ["库存", "相机", "三脚架", "投影仪", "还有"]
    retrieve = ["借", "期限", "多久", "几天", "规则"]
    if scheme == "library_adapted":
        inventory += ["馆藏", "可借册数", "在架"]
        retrieve += ["读者证", "续借", "归还", "无障碍"]
    if any(word in text for word in inventory):
        return "inventory"
    if any(word in text for word in ("费用", "多少钱", "逾期", "滞纳")):
        return "calculator"
    if any(word in text for word in retrieve):
        return "retrieve"
    return "human"


def _compare_transfer(rows: list[dict]) -> tuple[dict, list[dict]]:
    records = []
    for row in rows:
        original = _transfer_route(row["text"], "campus_original")
        adapted = _transfer_route(row["text"], "library_adapted")
        records.append({
            "id": row["id"], "condition": row["condition"], "text": row["text"],
            "expected_route": row["expected_route"], "original_route": original,
            "original_correct": original == row["expected_route"], "adapted_route": adapted,
            "adapted_correct": adapted == row["expected_route"],
        })
    comparison = {
        "original": {"correct": sum(row["original_correct"] for row in records), "n": len(records)},
        "adapted": {"correct": sum(row["adapted_correct"] for row in records), "n": len(records)},
    }
    return comparison, records


def run_s29(data: dict, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    rows = [dict(row) for row in data["transfer_requests"] if row["split"] == config["split"]]
    provided_comparison, _ = _compare_transfer(rows)
    added_request = config.get("added_request")
    if added_request is not None:
        _require(isinstance(added_request, dict), "added_request 应为对象")
        required = {"id", "condition", "text", "expected_route"}
        _require(required <= added_request.keys(), "added_request 缺少 id、condition、text 或 expected_route")
        _require(added_request["id"] not in {row["id"] for row in rows}, "added_request.id 不能与已有编号重复")
        _require(added_request["expected_route"] in {"retrieve", "inventory", "calculator", "human"}, "added_request.expected_route 不合法")
        rows.append({"split": config["split"], **added_request})
    comparison, records = _compare_transfer(rows)
    result = {
        "lesson": "S29", "project_id": data["project_id"],
        "new_user": "社区图书馆服务人员和读者",
        "new_use": "把文字请求送到查规则、查馆藏、算费用或人工处理路线",
        "comparison": comparison,
        "provided_comparison": provided_comparison,
        "added_request_id": added_request["id"] if added_request is not None else None,
        "new_metric": "同一批新场景请求上的路线正确数/请求总数，并单列涉及账户或个人信息的人工处理记录",
        "uncovered_condition": data["transfer_uncovered_condition"],
        "evidence_boundary": "provided_comparison 只覆盖课程编写者制作的 8 条中文请求；added_request 是学生自设计的单条检查。两者都不能推广到真实图书馆或其他未覆盖输入。",
    }
    return result, {"transfer_records": records}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _portable_path(path: Path, root: Path, placeholder: str) -> str:
    """仓库内文件写相对路径，仓库外路径写可替换占位符。"""
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return placeholder


def run_s30(data: dict, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    if "delivery_requests" in data:
        evaluation_stage = "final_evaluation"
        rows = [row for row in data["delivery_requests"] if row["split"] == evaluation_stage]
    else:
        evaluation_stage = "development"
        rows = [row for row in data["transfer_requests"] if row["split"] == evaluation_stage]
    _require(rows, f"{evaluation_stage} 没有可评价的请求")
    comparison, records = _compare_transfer(rows)
    release_candidate = config["release_candidate"]
    candidate_key = {
        "campus_original": "original",
        "library_adapted": "adapted",
    }.get(release_candidate)
    _require(
        candidate_key is not None,
        "release_candidate 应为 campus_original 或 library_adapted",
    )
    changed = [row["id"] for row in records if row["original_route"] != row["adapted_route"]]
    result = {
        "lesson": "S30", "project_id": data["project_id"],
        "evaluation_stage": evaluation_stage,
        "release_candidate": release_candidate,
        "selected_candidate_evaluation": {
            "scheme": candidate_key,
            **comparison[candidate_key],
        },
        "final_evaluation" if evaluation_stage == "final_evaluation" else "development_comparison": comparison,
        "changed_request_ids": changed,
        "evaluation_boundary": (
            "这是开发证据，可以用来选择并固定候选；它不是最后评价。"
            if evaluation_stage == "development"
            else "候选、指标和停止条件固定后才使用这批请求；看过结果后，它不能再次充当未见的最后评价。"
        ),
        "remaining_uncertainty": data["transfer_uncovered_condition"],
        "decision_owner": "程序保留证据，不替学生决定继续、修改或停止。",
    }
    return result, {"delivery_records": records}


RUNNERS = {"S25": run_s25, "S26": run_s26, "S27": run_s27, "S28": run_s28, "S29": run_s29, "S30": run_s30}


def run(lesson: str, data: dict, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    _require(lesson in RUNNERS, f"不支持课次：{lesson}")
    _validate(data, lesson)
    return RUNNERS[lesson](data, config)


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    fields = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(value, ensure_ascii=False, sort_keys=True)
                if isinstance(value, (dict, list)) else value
                for key, value in row.items()
            })


TABLE_FILES = {
    "S25": {"rounds": "rounds.csv", "episodes": "episodes.csv"},
    "S26": {"trajectories": "trajectories.csv"},
    "S27": {"monitoring_records": "records.csv", "batch_metrics": "batch_metrics.csv"},
    "S28": {"records": "records.csv", "timings": "timings.csv", "changed_records": "changed_records.csv"},
    "S29": {"transfer_records": "records.csv"},
    "S30": {"delivery_records": "records.csv"},
}


def _main(folder: Path) -> None:
    number = int(folder.name.split("-")[-1])
    lesson = LESSON_BY_NUMBER[number]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=folder / "data" / "base.json")
    parser.add_argument(
        "--final-data",
        type=Path,
        default=None,
        help="S30 在候选、指标和停止条件固定后显式传入的最后评价数据；默认不读取",
    )
    parser.add_argument("--config", type=Path, default=folder / "config.json")
    parser.add_argument("--output", type=Path, default=folder / "artifacts")
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    if args.final_data is not None:
        final_data = json.loads(args.final_data.read_text(encoding="utf-8"))
        _require(final_data.get("project_id") == data.get("project_id"), "最后评价 project_id 与基础数据不一致")
        data.update({key: value for key, value in final_data.items() if key not in {"kind", "project_id", "source"}})
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result, tables = run(lesson, data, config)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, rows in tables.items():
        _write_csv(args.output / TABLE_FILES[lesson][name], rows)
    if lesson == "S30":
        repository_root = folder.parent
        run_command = [
            "python", _portable_path(folder / "analysis.py", repository_root, "<ANALYSIS_FILE>"),
            "--data", _portable_path(args.data, repository_root, "<DATA_FILE>"),
        ]
        if args.final_data is not None:
            run_command.extend([
                "--final-data", _portable_path(args.final_data, repository_root, "<FINAL_DATA_FILE>"),
            ])
        run_command.extend([
            "--config", _portable_path(args.config, repository_root, "<CONFIG_FILE>"),
            "--output", "<OUTPUT_DIR>",
        ])
        manifest = {
            "lesson": lesson,
            "project_id": data["project_id"],
            "evaluation_stage": result["evaluation_stage"],
            "data_sha256": _sha256(args.data),
            "config_sha256": _sha256(args.config),
            "run_command": run_command,
            "run_command_note": "从学生仓库根目录运行；把尖括号占位符替换为本机路径。输出目录不是计算输入，因此固定记为 <OUTPUT_DIR>。",
            "outputs": ["summary.json", "records.csv"],
            "output_sha256": {
                "summary.json": _sha256(args.output / "summary.json"),
                "records.csv": _sha256(args.output / "records.csv"),
            },
            "deterministic": True,
        }
        if args.final_data is not None:
            manifest["final_data_sha256"] = _sha256(args.final_data)
        (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{lesson} 已生成：{args.output}")


def main(folder: Path) -> None:
    try:
        _main(folder)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"运行失败：{error}。以前的输出没有更新，不能当作本次结果。", file=sys.stderr)
        raise SystemExit(2) from error
