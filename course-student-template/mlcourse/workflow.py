"""S19–S24 共用的离线多步流程实验。

六课使用同一个校园设备请求作品。程序保留路由、资料、工具、权限、
人工交接和停止原因。它不是语言模型，也不把规则程序声称为智能体。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from collections import Counter
from pathlib import Path


LESSON_IDS = {
    "lesson-21": "S19",
    "lesson-22": "S20",
    "lesson-23": "S21",
    "lesson-24": "S22",
    "lesson-25": "S23",
    "lesson-26": "S24",
}
ROUTES = ("retrieve", "inventory", "calculator", "human")
ALLOWED_ACTIONS = {"read_public", "inventory_lookup", "calculate_fee"}


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{path} 第 {error.lineno} 行第 {error.colno} 列 JSON 格式有误"
        ) from error
    if not isinstance(value, dict):
        raise ValueError(f"{path} 顶层必须是对象")
    return value


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _require_number(value: object, name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} 必须是数值")


def _validate(data: dict, config: dict) -> None:
    requests = data.get("requests")
    documents = data.get("documents")
    if not isinstance(requests, list) or not requests:
        raise ValueError("requests 必须是非空数组")
    if not isinstance(documents, list) or not documents:
        raise ValueError("documents 必须是非空数组")

    request_ids = [row.get("id") for row in requests]
    if None in request_ids or len(request_ids) != len(set(request_ids)):
        raise ValueError("每条请求必须有不重复的 id")
    document_ids = [row.get("id") for row in documents]
    if None in document_ids or len(document_ids) != len(set(document_ids)):
        raise ValueError("每份资料必须有不重复的 id")
    known_documents = set(document_ids)

    for row in requests:
        route = row.get("expected_route")
        if route not in ROUTES:
            raise ValueError("expected_route 只能是 retrieve、inventory、calculator 或 human")
        if row.get("split") not in {"development", "holdout"}:
            raise ValueError("split 只能是 development 或 holdout")
        if row.get("batch") not in {"initial", "later", "final"}:
            raise ValueError("batch 只能是 initial、later 或 final")
        if not isinstance(row.get("text"), str) or not row["text"].strip():
            raise ValueError(f"{row.get('id')}：text 必须是非空文字")
        if route == "retrieve" and row.get("expected_document") not in known_documents:
            raise ValueError(f"{row['id']}：retrieve 请求的 expected_document 不存在")
        if route == "inventory" and not isinstance(row.get("item"), str):
            raise ValueError(f"{row['id']}：inventory 请求需要 item")
        if route == "calculator":
            _require_number(row.get("days"), f"{row['id']}.days")

    direct = data.get("direct_baseline")
    if not isinstance(direct, dict):
        raise ValueError("direct_baseline 必须是对象")
    for key in ("loan_days", "inventory_count", "fee_per_day"):
        _require_number(direct.get(key), f"direct_baseline.{key}")

    training = data.get("route_training")
    if not isinstance(training, list) or not training:
        raise ValueError("route_training 必须是非空数组")
    for row in training:
        if row.get("route") not in ROUTES or not isinstance(row.get("text"), str):
            raise ValueError("route_training 的 text/route 无效")

    cases = data.get("security_cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("security_cases 必须是非空数组")
    case_ids = [row.get("id") for row in cases]
    if None in case_ids or len(case_ids) != len(set(case_ids)):
        raise ValueError("每个安全案例必须有不重复的 id")
    for case in cases:
        if case.get("document_id") not in known_documents:
            raise ValueError(f"{case.get('id')}：document_id 指向不存在的资料")
        if not isinstance(case.get("requested_action"), str):
            raise ValueError(f"{case.get('id')}：requested_action 必须是文字")

    phrases = data.get("document_action_phrases")
    if (
        not isinstance(phrases, dict)
        or not phrases
        or any(not isinstance(k, str) or not isinstance(v, str) for k, v in phrases.items())
    ):
        raise ValueError("document_action_phrases 必须是‘文字片段→动作名’的非空对象")

    if not isinstance(config.get("seed"), int) or isinstance(config.get("seed"), bool):
        raise ValueError("seed 必须是整数")


def _keywords(text: str) -> set[str]:
    """透明的中文关键词表示；按连续片段匹配，不冒充通用语义表示。"""
    dictionary = {
        "借用", "借", "期限", "多久", "几天", "相机", "三脚架", "库存", "还有",
        "逾期", "费用", "多少钱", "密码", "账户", "导出", "修改", "预约", "教师",
        "学生", "菜单", "规则", "设备", "一天", "两天", "三天", "说明", "投影仪",
    }
    return {word for word in dictionary if word in text}


def _route_rule(text: str) -> str:
    if any(word in text for word in ("密码", "账户", "导出", "修改", "预约", "食堂")):
        return "human"
    if any(word in text for word in ("库存", "相机", "三脚架", "还有", "投影仪")):
        return "inventory"
    if any(word in text for word in ("费用", "多少钱", "逾期")):
        return "calculator"
    if any(word in text for word in ("借", "期限", "多久", "几天", "规则")):
        return "retrieve"
    return "human"


def _fixed_route(text: str) -> tuple[str, list[dict]]:
    """按预定顺序检查条件，并返回每个实际检查。"""
    checks = [
        ("human", ("密码", "账户", "导出", "修改", "预约", "食堂")),
        ("inventory", ("库存", "相机", "三脚架", "还有", "投影仪")),
        ("calculator", ("费用", "多少钱", "逾期")),
        ("retrieve", ("借", "期限", "多久", "几天", "规则")),
    ]
    visited = []
    for route, words in checks:
        matched = any(word in text for word in words)
        visited.append({"action": "route_check", "checked_route": route, "matched": matched})
        if matched:
            return route, visited
    return "human", visited


def _fit_router(examples: list[dict]) -> dict:
    """训练一个可追踪的多项式朴素贝叶斯路由器。"""
    by_route: dict[str, Counter] = {route: Counter() for route in ROUTES}
    totals = Counter()
    docs = Counter()
    vocab: set[str] = set()
    for row in examples:
        route = row["route"]
        tokens = _keywords(row["text"])
        # 集合不保留顺序。固定词元顺序，避免后续浮点数累加受
        # Python 进程的随机哈希顺序影响。
        by_route[route].update(sorted(tokens))
        totals[route] += len(tokens)
        docs[route] += 1
        vocab.update(tokens)
    return {"counts": by_route, "totals": totals, "docs": docs, "vocab": vocab}


def _predict_route(model: dict, text: str) -> tuple[str, float, dict[str, float]]:
    tokens = _keywords(text)
    vocab_size = max(1, len(model["vocab"]))
    n_docs = sum(model["docs"].values())
    scores = {}
    for route in ROUTES:
        prior = (model["docs"][route] + 1) / (n_docs + len(ROUTES))
        score = math.log(prior)
        denominator = model["totals"][route] + vocab_size
        # 相同对数项若以不同顺序相加，浮点数最末几位可能不同。课程 CI
        # 会逐字节比较产物，因此跨进程统一使用排序后的词元。
        for token in sorted(tokens):
            score += math.log((model["counts"][route][token] + 1) / denominator)
        scores[route] = score
    high = max(scores.values())
    exp = {route: math.exp(value - high) for route, value in scores.items()}
    total = sum(exp.values())
    probabilities = {route: exp[route] / total for route in ROUTES}
    route = max(ROUTES, key=lambda item: (probabilities[item], -ROUTES.index(item)))
    return route, probabilities[route], probabilities


def _retrieve(data: dict, text: str, *, filter_untrusted: bool = True) -> dict | None:
    query = _keywords(text)
    candidates = []
    for document in data["documents"]:
        if not document.get("active", False):
            continue
        if filter_untrusted and not document.get("trusted", False):
            continue
        overlap = len(query & set(document.get("keywords", [])))
        if overlap:
            candidates.append((overlap, document["id"], document))
    return max(candidates, default=(0, "", None), key=lambda item: (item[0], item[1]))[2]


def _tool_call(data: dict, name: str, arguments: dict, *, validate: bool = True) -> dict:
    if name == "inventory_lookup":
        item = arguments.get("item")
        if validate and item not in data["inventory"]:
            return {"ok": False, "error": "未知设备；没有执行查询"}
        if item not in data["inventory"]:
            return {"ok": False, "error": "查询失败"}
        return {"ok": True, "value": data["inventory"][item], "unit": "件"}
    if name == "overdue_fee":
        days = arguments.get("days")
        if validate and (not isinstance(days, int) or isinstance(days, bool) or not 0 <= days <= 30):
            return {"ok": False, "error": "days 必须是 0 到 30 的整数；没有执行计算"}
        if not isinstance(days, (int, float)) or isinstance(days, bool):
            return {"ok": False, "error": "计算失败"}
        return {"ok": True, "value": days * data["fee_per_day"], "unit": "元"}
    return {"ok": False, "error": "工具不在允许列表；没有执行"}


def _arguments(row: dict, route: str) -> tuple[str, dict]:
    """按实际选择的路线组装参数，不读取评价标签决定动作。"""
    if route == "inventory":
        return "inventory_lookup", {"item": row.get("item")}
    if route == "calculator":
        return "overdue_fee", {"days": row.get("days")}
    return "", {}


def _expected_value(row: dict) -> str:
    value = row.get("expected_value")
    return "" if value is None else str(value)


def _assess(row: dict, trace: dict) -> dict:
    """分开自动结果、适当交人和保守转人；未观察的人工结果不记为答错。"""
    route = trace["route"]
    expected_route = row["expected_route"]
    trace["expected_route"] = expected_route
    trace["expected_value"] = row.get("expected_value")
    trace["expected_document"] = row.get("expected_document")
    if not trace.get("covered", True):
        trace.update({
            "status": "not_covered",
            "automatic_correct": None,
            "reference_route_match": route == expected_route,
            "final_outcome_known": False,
        })
        return trace
    if route == "human":
        appropriate = expected_route == "human"
        trace.update({
            "status": "appropriate_handoff" if appropriate else "deferred_to_human",
            "automatic_correct": None,
            "reference_route_match": appropriate,
            "final_outcome_known": False,
        })
        return trace
    correct = route == expected_route and str(trace.get("answer_value")) == _expected_value(row)
    trace.update({
        "status": "automatic_correct" if correct else "automatic_error",
        "automatic_correct": correct,
        "reference_route_match": route == expected_route,
        "final_outcome_known": True,
    })
    return trace


def _execute(
    data: dict,
    row: dict,
    route: str,
    *,
    filter_untrusted: bool = True,
    validate_tools: bool = True,
    forced_document: dict | None = None,
    forced_tool: dict | None = None,
) -> dict:
    """执行一条路线并保留中间值。human 只形成待人工处理记录。"""
    trace = {
        "id": row["id"],
        "input_text": row["text"],
        "route": route,
        "retrieved_document": None,
        "tool": None,
        "tool_result": None,
        "answer_value": None,
        "needs_human": False,
        "covered": True,
    }
    if route == "retrieve":
        document = forced_document if forced_document is not None else _retrieve(
            data, row["text"], filter_untrusted=filter_untrusted
        )
        trace["retrieved_document"] = document["id"] if document else None
        trace["answer_value"] = document.get("answer_value") if document else None
    elif route in {"inventory", "calculator"}:
        name, arguments = _arguments(row, route)
        result = forced_tool if forced_tool is not None else _tool_call(
            data, name, arguments, validate=validate_tools
        )
        trace["tool"] = name
        trace["tool_arguments"] = arguments
        trace["tool_result"] = result
        trace["answer_value"] = result.get("value") if result.get("ok") else None
    else:
        trace["needs_human"] = True
    return _assess(row, trace)


def _direct_response(data: dict, row: dict) -> dict:
    """透明的一步基线：用固定默认值直接回复，不查资料或工具。"""
    policy = data["direct_baseline"]
    route = _route_rule(row["text"])
    human_markers = ("密码", "账户", "导出", "修改", "预约", "食堂")
    trace = {
        "id": row["id"],
        "input_text": row["text"],
        "route": route,
        "retrieved_document": None,
        "tool": None,
        "tool_result": None,
        "answer_value": None,
        "needs_human": route == "human",
        "covered": True,
        "baseline_rule": None,
    }
    if route == "retrieve":
        trace["answer_value"] = policy["loan_days"]
        trace["baseline_rule"] = "所有借用请求都回答固定天数"
    elif route == "inventory":
        trace["answer_value"] = policy["inventory_count"]
        trace["baseline_rule"] = "所有库存请求都回答固定件数"
    elif route == "calculator":
        days = row.get("days")
        if not isinstance(days, (int, float)) or isinstance(days, bool):
            trace["covered"] = False
            trace["baseline_rule"] = "缺少天数，一步基线无结果"
        else:
            trace["answer_value"] = days * policy["fee_per_day"]
            trace["baseline_rule"] = "天数×固定每日估计费用"
    else:
        if any(marker in row["text"] for marker in human_markers):
            trace["baseline_rule"] = "明确的权限或服务范围外请求交人"
        else:
            trace["covered"] = False
            trace["needs_human"] = False
            trace["baseline_rule"] = "文字没有匹配一步基线规则，因此没有结果"
    return _assess(row, trace)


def _summarize(traces: list[dict]) -> dict:
    automatic = [row for row in traces if row["status"] in {"automatic_correct", "automatic_error"}]
    automatic_correct = sum(row["status"] == "automatic_correct" for row in automatic)
    return {
        "n": len(traces),
        "covered": sum(row["status"] != "not_covered" for row in traces),
        "not_covered": sum(row["status"] == "not_covered" for row in traces),
        "automatic_count": len(automatic),
        "automatic_correct": automatic_correct,
        "automatic_errors": len(automatic) - automatic_correct,
        "automatic_accuracy": automatic_correct / len(automatic) if automatic else None,
        "sent_to_human": sum(bool(row["needs_human"]) for row in traces),
        "appropriate_handoffs": sum(row["status"] == "appropriate_handoff" for row in traces),
        "deferred_automatable": sum(row["status"] == "deferred_to_human" for row in traces),
        "reference_route_matches": sum(bool(row["reference_route_match"]) for row in traces),
    }


def _select_requests(data: dict, *, split: str, batch: str | None = None) -> list[dict]:
    rows = [row for row in data["requests"] if row["split"] == split]
    if batch is not None:
        rows = [row for row in rows if row["batch"] == batch]
    if not rows:
        suffix = f"、batch={batch}" if batch else ""
        raise ValueError(f"数据中没有 split={split}{suffix} 的请求")
    return rows


def run_s19(data: dict, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    batch = config.get("request_batch")
    if batch not in {"initial", "later"}:
        raise ValueError("request_batch 只能是 initial 或 later")
    rows = _select_requests(data, split="development", batch=batch)
    direct, pipeline, comparisons = [], [], []
    for row in rows:
        direct_trace = _direct_response(data, row)
        pipeline_trace = _execute(data, row, _route_rule(row["text"]))
        direct.append(direct_trace)
        pipeline.append(pipeline_trace)
        comparisons.append({
            "id": row["id"],
            "input_text": row["text"],
            "expected_route": row["expected_route"],
            "expected_value": row.get("expected_value"),
            "direct_route": direct_trace["route"],
            "direct_rule": direct_trace["baseline_rule"],
            "direct_value": direct_trace["answer_value"],
            "direct_status": direct_trace["status"],
            "pipeline_route": pipeline_trace["route"],
            "pipeline_document": pipeline_trace["retrieved_document"],
            "pipeline_tool": pipeline_trace["tool"],
            "pipeline_tool_result": pipeline_trace["tool_result"],
            "pipeline_value": pipeline_trace["answer_value"],
            "pipeline_status": pipeline_trace["status"],
        })
    result = {
        "lesson": "S19",
        "request_batch": batch,
        "comparison": {
            "direct_response": _summarize(direct),
            "step_pipeline": _summarize(pipeline),
        },
        "direct_baseline": data["direct_baseline"],
        "main_relation": "分步流程留下可核对的中间结果；一步基线是透明固定规则，未覆盖输入单独记录",
        "limits": "这是确定性教学流程，没有调用语言模型；只验证步骤与中间产物。",
    }
    return result, {"traces": comparisons}


def run_s20(data: dict, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    if not isinstance(config.get("validate_arguments"), bool):
        raise ValueError("validate_arguments 必须是布尔值")
    invalid_call = config.get("invalid_call")
    if not isinstance(invalid_call, dict) or not isinstance(invalid_call.get("arguments"), dict):
        raise ValueError("invalid_call 需要 tool 和 arguments")
    rows = [
        row for row in _select_requests(data, split="development")
        if row["expected_route"] in {"inventory", "calculator"}
    ]
    records, direct_traces, tool_traces = [], [], []
    for row in rows:
        direct = _direct_response(data, row)
        tool = _execute(data, row, row["expected_route"], validate_tools=config["validate_arguments"])
        direct_traces.append(direct)
        tool_traces.append(tool)
        records.append({
            "id": row["id"],
            "tool": tool["tool"],
            "arguments": tool.get("tool_arguments"),
            "direct_rule": direct["baseline_rule"],
            "direct_value": direct["answer_value"],
            "direct_status": direct["status"],
            "tool_ok": bool(tool["tool_result"] and tool["tool_result"].get("ok")),
            "tool_value": tool["answer_value"],
            "tool_unit": tool["tool_result"].get("unit") if tool["tool_result"] else None,
            "tool_status": tool["status"],
            "expected_value": row.get("expected_value"),
            "error": tool["tool_result"].get("error") if tool["tool_result"] else None,
        })
    invalid = _tool_call(
        data,
        invalid_call.get("tool", ""),
        invalid_call["arguments"],
        validate=True,
    )
    result = {
        "lesson": "S20",
        "comparison": {
            "direct_response": _summarize(direct_traces),
            "tool_result": _summarize(tool_traces),
        },
        "invalid_call": {**invalid_call, "result": invalid},
        "limits": "工具是本地只读查询与计算；没有修改真实库存或账户。",
    }
    return result, {"tool_calls": records}


def _add_action(actions: list[dict], scheme: str, row: dict, **values: object) -> None:
    actions.append({
        "scheme": scheme,
        "id": row["id"],
        "action_index": len(actions) + 1,
        "action": values.pop("action"),
        "route": values.pop("route", None),
        "outcome": values.pop("outcome", None),
        **values,
    })


def _bounded_execution(
    data: dict,
    row: dict,
    *,
    scheme: str,
    route: str,
    routing_actions: list[dict],
    max_tool_retries: int,
    max_actions: int,
    stop_when_complete: bool,
    failure_request_id: str,
) -> tuple[dict, list[dict]]:
    actions: list[dict] = []
    for item in routing_actions:
        if len(actions) >= max_actions:
            break
        _add_action(actions, scheme, row, **item)
    if len(actions) >= max_actions:
        final = _execute(data, row, "human")
        final.update({
            "attempted_route": route,
            "action_count": len(actions),
            "retries_used": 0,
            "tool_failures": 0,
            "repeated_after_completion": 0,
            "stopped_reason": "action_budget_exhausted",
        })
        return final, actions

    if route == "human":
        final = _execute(data, row, "human")
        _add_action(actions, scheme, row, action="handoff", route="human", outcome=final["status"])
        final.update({
            "attempted_route": route,
            "action_count": len(actions),
            "retries_used": 0,
            "tool_failures": 0,
            "repeated_after_completion": 0,
            "stopped_reason": "sent_to_human",
        })
        return final, actions

    retries_used = 0
    tool_failures = 0
    repeated = 0
    first_attempt = True
    final: dict | None = None
    while len(actions) < max_actions:
        forced_tool = None
        if route in {"inventory", "calculator"} and row["id"] == failure_request_id and first_attempt:
            forced_tool = {"ok": False, "error": "课程模拟：首次工具调用超时"}
        current = _execute(data, row, route, forced_tool=forced_tool)
        failed_tool = bool(current.get("tool_result")) and not current["tool_result"].get("ok", False)
        if failed_tool:
            tool_failures += 1
        _add_action(
            actions,
            scheme,
            row,
            action="retrieve" if route == "retrieve" else "tool_call",
            route=route,
            outcome="tool_failure" if failed_tool else current["status"],
            answer_value=current.get("answer_value"),
            is_retry=not first_attempt,
            is_repeat_after_completion=False,
        )
        first_attempt = False
        if failed_tool:
            if retries_used < max_tool_retries and len(actions) < max_actions:
                retries_used += 1
                continue
            final = _execute(data, row, "human")
            if len(actions) < max_actions:
                _add_action(
                    actions,
                    scheme,
                    row,
                    action="handoff_after_failure",
                    route="human",
                    outcome=final["status"],
                )
            final["stopped_reason"] = "retry_limit_reached"
            break

        final = current
        if stop_when_complete:
            final["stopped_reason"] = "completed"
            break
        if len(actions) < max_actions:
            repeated_trace = _execute(data, row, route)
            repeated += 1
            _add_action(
                actions,
                scheme,
                row,
                action="retrieve" if route == "retrieve" else "tool_call",
                route=route,
                outcome=repeated_trace["status"],
                answer_value=repeated_trace.get("answer_value"),
                is_retry=False,
                is_repeat_after_completion=True,
            )
            final = repeated_trace
            final["stopped_reason"] = "stopped_after_one_redundant_repeat"
        else:
            final["stopped_reason"] = "action_budget_exhausted"
        break

    if final is None:
        final = _execute(data, row, "human")
        final["stopped_reason"] = "action_budget_exhausted"
    final.update({
        "attempted_route": route,
        "action_count": len(actions),
        "retries_used": retries_used,
        "tool_failures": tool_failures,
        "repeated_after_completion": repeated,
    })
    return final, actions


def _workflow_summary(traces: list[dict]) -> dict:
    return {
        **_summarize(traces),
        "total_actions": sum(row["action_count"] for row in traces),
        "tool_failures": sum(row["tool_failures"] for row in traces),
        "retries_used": sum(row["retries_used"] for row in traces),
        "repeated_after_completion": sum(row["repeated_after_completion"] for row in traces),
    }


def run_s21(data: dict, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    batch = config.get("request_batch")
    if batch not in {"initial", "later"}:
        raise ValueError("request_batch 只能是 initial 或 later")
    threshold = config.get("confidence_threshold")
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or not 0 <= threshold <= 1:
        raise ValueError("confidence_threshold 必须在 0 到 1")
    retries = config.get("max_tool_retries")
    max_actions = config.get("max_actions")
    if not isinstance(retries, int) or isinstance(retries, bool) or not 0 <= retries <= 3:
        raise ValueError("max_tool_retries 必须是 0 到 3 的整数")
    if not isinstance(max_actions, int) or isinstance(max_actions, bool) or not 2 <= max_actions <= 12:
        raise ValueError("max_actions 必须是 2 到 12 的整数")
    if not isinstance(config.get("stop_when_complete"), bool):
        raise ValueError("stop_when_complete 必须是布尔值")
    failure_request_id = config.get("failure_request_id")
    if not isinstance(failure_request_id, str):
        raise ValueError("failure_request_id 必须是请求编号")

    model = _fit_router(data["route_training"])
    rows = _select_requests(data, split="development", batch=batch)
    if failure_request_id not in {row["id"] for row in rows}:
        raise ValueError("failure_request_id 必须属于当前批次")
    fixed, dynamic, decisions, action_trace = [], [], [], []
    for row in rows:
        fixed_route, fixed_checks = _fixed_route(row["text"])
        fixed_trace, fixed_actions = _bounded_execution(
            data,
            row,
            scheme="fixed",
            route=fixed_route,
            routing_actions=fixed_checks,
            max_tool_retries=retries,
            max_actions=max_actions,
            stop_when_complete=config["stop_when_complete"],
            failure_request_id=failure_request_id,
        )
        fixed.append(fixed_trace)
        action_trace.extend(fixed_actions)

        predicted, confidence, probabilities = _predict_route(model, row["text"])
        route = predicted if confidence >= threshold else "human"
        model_routing = [{
            "action": "model_route",
            "route": route,
            "outcome": "selected" if route != "human" else "below_threshold_handoff",
            "confidence": confidence,
        }]
        dynamic_trace, dynamic_actions = _bounded_execution(
            data,
            row,
            scheme="model",
            route=route,
            routing_actions=model_routing,
            max_tool_retries=retries,
            max_actions=max_actions,
            stop_when_complete=config["stop_when_complete"],
            failure_request_id=failure_request_id,
        )
        dynamic.append(dynamic_trace)
        action_trace.extend(dynamic_actions)
        decisions.append({
            "id": row["id"],
            "text": row["text"],
            "predicted_route": predicted,
            "confidence": confidence,
            "executed_route": route,
            "expected_route": row["expected_route"],
            "status": dynamic_trace["status"],
            "automatic_correct": dynamic_trace["automatic_correct"],
            "sent_to_human": dynamic_trace["needs_human"],
            "action_count": dynamic_trace["action_count"],
            "tool_failures": dynamic_trace["tool_failures"],
            "retries_used": dynamic_trace["retries_used"],
            "repeated_after_completion": dynamic_trace["repeated_after_completion"],
            "stopped_reason": dynamic_trace["stopped_reason"],
            **{f"p_{key}": probabilities[key] for key in ROUTES},
        })
    result = {
        "lesson": "S21",
        "action_unit": "一次路由条件检查、一次模型路由决定、一次检索、一次工具调用或一次交人，均记 1 个动作",
        "comparison": {
            "fixed": _workflow_summary(fixed),
            "model_routed": _workflow_summary(dynamic),
        },
        "router": "由 route_training 训练的多项式朴素贝叶斯分类器",
        "failure_case": failure_request_id,
        "stop_rule": {
            "stop_when_complete": config["stop_when_complete"],
            "max_tool_retries": retries,
            "max_actions": max_actions,
        },
        "limits": "这是小型分类模型选路线的受限教学流程，不是语言模型智能体。",
    }
    return result, {"route_decisions": decisions, "action_trace": action_trace}


def _extract_document_action(data: dict, text: str) -> tuple[str | None, str | None]:
    """用数据中公开的字面短语表提取动作，不冒充语义理解。"""
    for phrase in sorted(data["document_action_phrases"], key=len, reverse=True):
        if phrase in text:
            return data["document_action_phrases"][phrase], phrase
    return None, None


def _permission(action: str) -> bool:
    return action in ALLOWED_ACTIONS


def run_s22(data: dict, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    follow = config.get("follow_document_instructions")
    if not isinstance(follow, bool):
        raise ValueError("follow_document_instructions 必须是布尔值")
    documents = {item["id"]: item for item in data["documents"]}
    records = []
    for case in data["security_cases"]:
        document = documents[case["document_id"]]
        extracted, phrase = _extract_document_action(data, document["text"])
        use_extracted = follow and extracted is not None
        proposed = extracted if use_extracted else case["requested_action"]
        allowed = _permission(proposed)
        executed = proposed if allowed else "blocked"
        records.append({
            "id": case["id"],
            "document_id": document["id"],
            "document_trusted": document["trusted"],
            "document_text": document["text"],
            "matched_phrase": phrase,
            "extracted_document_action": extracted,
            "requested_action": case["requested_action"],
            "proposed_action_source": "document_text" if use_extracted else "user_request",
            "proposed_action": proposed,
            "permission_allowed": allowed,
            "executed_action": executed,
            "unsafe_executed": executed not in {"blocked", *ALLOWED_ACTIONS},
            "unexpected_action_executed": executed not in {"blocked", case["requested_action"]},
            "legitimate_request_completed": (
                case["requested_action"] in ALLOWED_ACTIONS and executed == case["requested_action"]
            ),
        })
    result = {
        "lesson": "S22",
        "metrics": {
            "cases": len(records),
            "blocked": sum(row["executed_action"] == "blocked" for row in records),
            "unsafe_executed": sum(row["unsafe_executed"] for row in records),
            "unexpected_action_executed": sum(row["unexpected_action_executed"] for row in records),
            "legitimate_request_completed": sum(row["legitimate_request_completed"] for row in records),
        },
        "recognized_phrases": data["document_action_phrases"],
        "main_relation": "检索到的文字属于数据；文字中的候选动作仍要经过独立权限检查",
        "limits": "字面提取只识别数据中列出的短语；执行器只写日志，没有真实外部副作用。",
    }
    return result, {"action_log": records}


def _pipeline_with_fault(data: dict, row: dict, fault: str | None, replacement: str | None) -> dict:
    route = _route_rule(row["text"])
    if fault == "route":
        route = "human" if row["expected_route"] != "human" else "retrieve"
    if replacement == "route":
        route = row["expected_route"]
    forced_document = None
    forced_tool = None
    if row["expected_route"] == "retrieve":
        if fault == "retrieve":
            forced_document = next((d for d in data["documents"] if d["id"] == "loan-old"), None)
        if replacement == "retrieve":
            forced_document = next((d for d in data["documents"] if d["id"] == row["expected_document"]), None)
    if row["expected_route"] in {"inventory", "calculator"}:
        if fault == "tool":
            forced_tool = {"ok": True, "value": -1, "unit": "错误单位"}
        if replacement == "tool":
            name, args = _arguments(row, row["expected_route"])
            forced_tool = _tool_call(data, name, args, validate=True)
    trace = _execute(data, row, route, forced_document=forced_document, forced_tool=forced_tool)
    if fault == "handoff" and trace["status"] == "automatic_correct":
        trace["answer_value"] = "交接时丢失"
        trace = _assess(row, trace)
    if replacement == "handoff" and route == row["expected_route"] and route != "human":
        trace["answer_value"] = row.get("expected_value")
        trace = _assess(row, trace)
    return trace


def _prefixed_trace(prefix: str, trace: dict) -> dict:
    tool = trace.get("tool_result") or {}
    return {
        f"{prefix}_route": trace.get("route"),
        f"{prefix}_document": trace.get("retrieved_document"),
        f"{prefix}_tool": trace.get("tool"),
        f"{prefix}_tool_ok": tool.get("ok"),
        f"{prefix}_tool_value": tool.get("value"),
        f"{prefix}_tool_error": tool.get("error"),
        f"{prefix}_needs_human": trace.get("needs_human"),
        f"{prefix}_answer_value": trace.get("answer_value"),
        f"{prefix}_status": trace.get("status"),
        f"{prefix}_automatic_correct": trace.get("automatic_correct"),
    }


def run_s23(data: dict, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    valid_stages = {"route", "retrieve", "tool", "handoff"}
    fault_stage = config.get("fault_stage")
    replacement_stage = config.get("replacement_stage")
    if fault_stage not in valid_stages or replacement_stage not in valid_stages:
        raise ValueError("fault_stage/replacement_stage 只能是 route、retrieve、tool 或 handoff")
    rows = _select_requests(data, split="development", batch="initial")
    base = [_pipeline_with_fault(data, row, None, None) for row in rows]
    broken = [_pipeline_with_fault(data, row, fault_stage, None) for row in rows]
    repaired = [
        _pipeline_with_fault(data, row, fault_stage, replacement_stage)
        for row in rows
    ]
    comparisons = []
    for row, original, faulted, replacement in zip(rows, base, broken, repaired, strict=True):
        comparisons.append({
            "id": row["id"],
            "expected_route": row["expected_route"],
            "expected_document": row.get("expected_document"),
            "expected_value": row.get("expected_value"),
            "fault_stage": fault_stage,
            "replacement_stage": replacement_stage,
            **_prefixed_trace("original", original),
            **_prefixed_trace("fault", faulted),
            **_prefixed_trace("replacement", replacement),
        })
    result = {
        "lesson": "S23",
        "comparison": {
            "original": _summarize(base),
            "with_fault": _summarize(broken),
            "with_one_replacement": _summarize(repaired),
        },
        "interpretation_rule": "替换某一步后局部值与端到端结果一起恢复，才支持该步是当前故障原因；一次结果仍可能有其他解释。",
    }
    return result, {"fault_comparison": comparisons}


def _candidate_settings(config: dict, candidate: bool) -> tuple[float, bool, bool]:
    prefix = "candidate" if candidate else "baseline"
    threshold = config.get(f"{prefix}_confidence_threshold")
    filter_untrusted = config.get(f"{prefix}_filter_untrusted")
    validate_tools = config.get(f"{prefix}_validate_tools")
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or not 0 <= threshold <= 1:
        raise ValueError(f"{prefix}_confidence_threshold 必须在 0 到 1")
    if not isinstance(filter_untrusted, bool) or not isinstance(validate_tools, bool):
        raise ValueError(f"{prefix} 的 filter_untrusted/validate_tools 必须是布尔值")
    return float(threshold), filter_untrusted, validate_tools


def _evaluate_candidate(data: dict, rows: list[dict], config: dict, candidate: bool) -> tuple[dict, list[dict]]:
    model = _fit_router(data["route_training"])
    threshold, filter_untrusted, validate_tools = _candidate_settings(config, candidate)
    traces = []
    for row in rows:
        predicted, confidence, _ = _predict_route(model, row["text"])
        route = predicted if confidence >= threshold else "human"
        trace = _execute(
            data,
            row,
            route,
            filter_untrusted=filter_untrusted,
            validate_tools=validate_tools,
        )
        trace["predicted_route"] = predicted
        trace["confidence"] = confidence
        traces.append(trace)
    return _summarize(traces), traces


def run_s24(data: dict, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    mode = config.get("evaluation_mode")
    if mode not in {"development", "final"}:
        raise ValueError("evaluation_mode 只能是 development 或 final")
    splits = {row["split"] for row in data["requests"]}
    expected_split = "development" if mode == "development" else "holdout"
    if splits != {expected_split}:
        raise ValueError(
            "development 模式只能使用开发数据文件，final 模式只能使用单独 holdout 文件"
        )
    _candidate_settings(config, False)
    _candidate_settings(config, True)
    changed = [
        key.removeprefix("candidate_")
        for key in config
        if key.startswith("candidate_")
        and config.get(key) != config.get("baseline_" + key.removeprefix("candidate_"))
    ]
    if len(changed) > 1:
        raise ValueError("公平比较一次只能改一项 candidate 设置")
    rows = _select_requests(data, split=expected_split)
    baseline_summary, baseline_traces = _evaluate_candidate(data, rows, config, False)
    candidate_summary, candidate_traces = _evaluate_candidate(data, rows, config, True)
    comparisons = []
    for request, baseline, candidate in zip(rows, baseline_traces, candidate_traces, strict=True):
        comparisons.append({
            "id": request["id"],
            "expected_route": request["expected_route"],
            "expected_value": request.get("expected_value"),
            "baseline_predicted_route": baseline["predicted_route"],
            "baseline_confidence": baseline["confidence"],
            "baseline_executed_route": baseline["route"],
            "baseline_document": baseline["retrieved_document"],
            "baseline_value": baseline["answer_value"],
            "baseline_status": baseline["status"],
            "candidate_predicted_route": candidate["predicted_route"],
            "candidate_confidence": candidate["confidence"],
            "candidate_executed_route": candidate["route"],
            "candidate_document": candidate["retrieved_document"],
            "candidate_value": candidate["answer_value"],
            "candidate_status": candidate["status"],
        })
    table_name = "development_cases" if mode == "development" else "final_cases"
    result = {
        "lesson": "S24",
        "evaluation_mode": mode,
        "data_role": expected_split,
        "comparison": {"baseline": baseline_summary, "candidate": candidate_summary},
        "changed_settings": changed,
        "decision": "由学生根据用途、错误记录和人工容量决定保留、修改或停止；程序不自动推荐。",
        "limits": (
            "本次只产生开发结果，没有读取或写出 holdout。"
            if mode == "development"
            else "本次只产生 holdout 最终结果；查看后再改设置必须另找新数据。"
        ),
    }
    return result, {table_name: comparisons}


RUNNERS = {
    "S19": run_s19,
    "S20": run_s20,
    "S21": run_s21,
    "S22": run_s22,
    "S23": run_s23,
    "S24": run_s24,
}


def run(lesson_id: str, data: dict, config: dict) -> tuple[dict, dict[str, list[dict]]]:
    if lesson_id not in RUNNERS:
        raise ValueError(f"未知课次：{lesson_id}")
    _validate(data, config)
    result, tables = RUNNERS[lesson_id](data, config)
    result["status"] = "example_only"
    result["config"] = config
    result["provenance"] = {"data_sha256": _digest(data), "config_sha256": _digest(config)}
    return result, tables


def main(lesson_directory: Path) -> int:
    parser = argparse.ArgumentParser(description="运行 S19–S24 共用的离线多步流程实验")
    parser.add_argument("--data", type=Path, default=lesson_directory / "data/base.json")
    parser.add_argument("--config", type=Path, default=lesson_directory / "config.json")
    parser.add_argument("--output", type=Path, default=lesson_directory / "artifacts")
    args = parser.parse_args()
    try:
        lesson_id = LESSON_IDS[lesson_directory.name]
        data, config = _read_json(args.data), _read_json(args.config)
        result, tables = run(lesson_id, data, config)
        result["provenance"].update({
            "data_file": os.path.relpath(args.data, Path.cwd()),
            "config_file": os.path.relpath(args.config, Path.cwd()),
            "workflow_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "entry_sha256": hashlib.sha256((lesson_directory / "analysis.py").read_bytes()).hexdigest(),
        })
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "summary.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        for name, records in tables.items():
            if not records:
                continue
            fields = list(dict.fromkeys(key for record in records for key in record))
            with (args.output / f"{name}.csv").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                for record in records:
                    writer.writerow({
                        key: json.dumps(value, ensure_ascii=False, sort_keys=True)
                        if isinstance(value, (dict, list)) else value
                        for key, value in record.items()
                    })
        print(f"{lesson_id} 示例实验完成：{args.output / 'summary.json'}")
        for name in tables:
            print(f"先查看：{args.output / (name + '.csv')}")
        return 0
    except (KeyError, TypeError, ValueError, OSError) as error:
        parser.exit(2, f"无法运行：{error}\n请核对数据字段和配置；旧输出不能代替本次运行。\n")
