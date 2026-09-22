"""S01–S06：任务、标签、划分、评价、补数据与单因素诊断。

使用可阅读的小计算，保留逐条证据；程序不替学生作出采用建议。
"""
from __future__ import annotations

from copy import deepcopy
import math
from statistics import mean
import numpy as np

from .foundations_data import CONFIGS, TITLES

NAMES = {"baseline": "均值基线", "rule": "人工规则", "linear": "一元线性回归",
         "no_action": "不提醒（不提供分钟预测）", "buffered": "回归预测加缓冲时间",
         "available_only": "只统计已收到的标签", "zero_fill_demo": "未知标签填零（错误示范）",
         "proxy_all": "全部使用代理标签", "time": "时间划分", "group": "分组划分",
         "random": "随机划分", "original": "原方案", "candidate": "修订候选",
         "no_addition": "不补数据", "random_sample": "随机补充", "group_first": "优先补指定时段",
         "synthetic": "模型生成标签（模拟）"}


def numeric(value, name, *, minimum=0.0, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} 必须是有限数值，不能是空值、文字或无穷大")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} 不能小于 {minimum}")
    if integer and int(value) != value:
        raise ValueError(f"{name} 必须是整数")
    return int(value) if integer else float(value)


def choice(config, key, allowed):
    value = config[key]
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(f"{key} 只能选择 {'、'.join(allowed)}")
    return value


def validate(lesson, data, config):
    expected = set(CONFIGS[lesson])
    if set(config) != expected:
        raise ValueError(f"配置字段不一致；缺少 {sorted(expected-set(config))}；未知 {sorted(set(config)-expected)}。请对照本课配置。")
    numeric(config["seed"], "seed", integer=True)
    if "evaluation_split" in config:
        choice(config, "evaluation_split", ("validation", "test"))
    kind = "foundation_label_audit" if lesson == "S02" else "foundation_sampling" if lesson == "S05" else "foundation_waiting"
    if data.get("kind") != kind:
        raise ValueError(f"请使用本课 data/base.json（kind={kind}）；换题时请一起修改程序。")
    rows = data.get("rows")
    if not isinstance(rows, list) or not 2 <= len(rows) <= 10000:
        raise ValueError("rows 需要 2 至 10000 条样本")
    seen = set()
    for r in rows:
        if not isinstance(r, dict):
            raise ValueError("每条样本应是带字段名的对象")
        required = {"id", "queue_length", "wait_minutes", "period", "site", "day"}
        if lesson == "S02":
            required |= {"available_day", "proxy_minutes", "review_minutes"}
        elif lesson == "S03":
            required |= {"receipt_minutes", "split"}
        else:
            required.add("split")
        for key in required:
            if key not in r:
                raise ValueError(f"样本 {r.get('id', '?')} 缺少字段：{key}")
        if not isinstance(r["id"], str) or not r["id"].strip() or r["id"] in seen:
            raise ValueError("样本 id 必须是非空且不重复的文字")
        seen.add(r["id"])
        if r["queue_length"] is not None or lesson != "S06":
            numeric(r["queue_length"], f"{r['id']}.queue_length（人数）", integer=True)
        if r["wait_minutes"] is not None or lesson != "S02":
            numeric(r["wait_minutes"], f"{r['id']}.wait_minutes（实际分钟数）")
        if r["period"] not in ("午间", "晚间"):
            raise ValueError("period 只能为午间或晚间；增加时段时请同时修改特征处理。")
        if not isinstance(r["site"], str) or not r["site"].strip():
            raise ValueError("site（窗口）必须是非空文字")
        numeric(r["day"], "day", minimum=1, integer=True)
        if "split" in required:
            allowed = ("train", "pool", "validation", "test") if lesson == "S05" else ("train", "validation", "test")
            if r["split"] not in allowed:
                raise ValueError(f"split 只能为 {'、'.join(allowed)}")
        if lesson == "S02":
            if (r["wait_minutes"] is None) != (r["available_day"] is None):
                raise ValueError("wait_minutes 和 available_day 应同时为 null，或同时给出数值")
            if r["available_day"] is not None:
                numeric(r["available_day"], "available_day", minimum=r["day"], integer=True)
            numeric(r["proxy_minutes"], "proxy_minutes")
            if r["review_minutes"] is not None:
                numeric(r["review_minutes"], "review_minutes")
        if lesson == "S03":
            numeric(r["receipt_minutes"], "receipt_minutes")
    return rows


def split_rows(rows, evaluation_split):
    train = [r for r in rows if r["split"] == "train"]
    evaluation = [r for r in rows if r["split"] == evaluation_split]
    if len(train) < 2 or not evaluation:
        raise ValueError("至少需要两条 train 样本及一条指定的验证或测试样本")
    return train, evaluation


def fit(train, features=("queue_length",), imputation="zero"):
    """只从训练集学习填补值和线性回归系数。测试集不参与任何参数计算。"""
    known = [r["queue_length"] for r in train if r["queue_length"] is not None]
    if len(train) < 2 or not known:
        raise ValueError("训练样本不足，或训练集人数全部缺失，无法学习填补值和模型")
    if len(set(known)) < 2 and features == ("queue_length",):
        raise ValueError("训练集至少需要两种不同人数，才能估计人数与等待时间的关系")
    model = dict(features=list(features), imputation=imputation,
                 fill_value=mean(known) if imputation == "mean" else 0.0,
                 train_ids=[r["id"] for r in train])
    x = design(train, model)
    y = np.asarray([r["wait_minutes"] for r in train], dtype=float)
    model["coefficients"] = np.linalg.lstsq(x, y, rcond=None)[0].tolist()
    return model


def design(rows, model):
    values = []
    for r in rows:
        v = [1.0]
        for f in model["features"]:
            if f == "evening":
                v.append(float(r["period"] == "晚间"))
            else:
                v.append(model["fill_value"] if r[f] is None else r[f])
        values.append(v)
    x = np.asarray(values, dtype=float)
    if not np.isfinite(x).all():
        raise ValueError("模型输入含无穷大或未处理的缺失值")
    return x


def predict(model, rows):
    p = design(rows, model) @ model["coefficients"]
    if not np.isfinite(p).all():
        raise ValueError("预测不是有限数值，请检查输入尺度")
    return p.tolist()


def errors(actual, predicted, under_weight=1.0):
    if not actual or len(actual) != len(predicted):
        raise ValueError("真实值和预测值必须非空、一一对应")
    e = np.asarray(predicted) - np.asarray(actual)
    return dict(n=len(actual), mae=float(np.abs(e).mean()), rmse=float(np.sqrt((e**2).mean())),
                asymmetric_loss=float(np.where(e < 0, -e*under_weight, e).mean()))


def comparisons_table(reports):
    return [dict(method=k, method_name=NAMES.get(k, k), **v) for k, v in reports.items()]


def output(primary, reports, rows, records, stress_change, stress_metrics, **details):
    return dict(metrics=reports[primary], comparison={k: v for k, v in reports.items() if k != primary},
                stress_test=dict(change=stress_change, metrics=stress_metrics),
                details=dict(primary_method=primary, tables=dict(records=records, comparison=comparisons_table(reports)),
                             evaluation_ids=[r["id"] for r in rows], **details))


def regression_reports(evaluation, predictions, under_weight=1.0):
    y = [r["wait_minutes"] for r in evaluation]
    reports = {k: errors(y, p, under_weight) for k, p in predictions.items()}
    records = []
    for name, ps in predictions.items():
        for r, p in zip(evaluation, ps):
            records.append(dict(id=r["id"], method=name, period=r["period"], queue_length=r["queue_length"],
                                actual=r["wait_minutes"], prediction=p, absolute_error=abs(p-r["wait_minutes"])))
    return reports, records


def grouped(evaluation, predictions):
    result = {}
    for period in sorted({r["period"] for r in evaluation}):
        indices = [i for i, r in enumerate(evaluation) if r["period"] == period]
        result[period] = {name: errors([evaluation[i]["wait_minutes"] for i in indices], [p[i] for i in indices])
                          for name, p in predictions.items()}
    return result


def s01(data, config):
    rows = validate("S01", data, config)
    primary = choice(config, "primary_model", ("baseline", "rule", "linear"))
    intercept = numeric(config["rule_intercept"], "rule_intercept")
    slope = numeric(config["rule_slope"], "rule_slope")
    threshold = numeric(config["alert_minutes"], "alert_minutes")
    stress_queue = numeric(config["stress_queue"], "stress_queue", integer=True)
    train, evaluation = split_rows(rows, config["evaluation_split"])
    model = fit(train)
    base = mean(r["wait_minutes"] for r in train)
    ps = dict(baseline=[base]*len(evaluation), rule=[intercept+slope*r["queue_length"] for r in evaluation],
              linear=predict(model, evaluation))
    reports, records = regression_reports(evaluation, ps)
    for name, predictions in ps.items():
        reports[name]["alerts"] = sum(p >= threshold for p in predictions)
    # 不提醒没有分钟预测；不能把它的回归误差写成 0。
    reports["no_action"] = dict(n=len(evaluation), mae=None, rmse=None, asymmetric_loss=None, alerts=0)
    for record in records:
        record["alert"] = record["prediction"] >= threshold
    new = {**evaluation[0], "queue_length": stress_queue}
    stress = dict(queue_length=stress_queue, actual=None,
                  predictions=dict(baseline=base, rule=intercept+slope*stress_queue, linear=predict(model, [new])[0]),
                  measured_intervention_effect=None)
    return output(primary, reports, evaluation, records, "只改变新输入人数，没有观察行动后的结果", stress,
                  evaluation_split=config["evaluation_split"], train_ids=model["train_ids"], model=model,
                  by_period=grouped(evaluation, ps), intervention_effect=None,
                  note="提醒数量不是节省分钟数；本实验没有测量提醒的因果效果。")


def s02(data, config):
    rows = validate("S02", data, config)
    day = numeric(config["observation_day"], "observation_day", minimum=max(r["day"] for r in rows), integer=True)
    later = numeric(config["later_day"], "later_day", minimum=day, integer=True)
    tolerance = numeric(config["disagreement_minutes"], "disagreement_minutes")

    def audit(cutoff):
        available = [r for r in rows if r["available_day"] is not None and r["available_day"] <= cutoff]
        paired = [r for r in available if r["review_minutes"] is not None]
        total = sum(r["wait_minutes"] for r in available)
        conflict = sum(abs(r["wait_minutes"] - r["review_minutes"]) > tolerance for r in paired)
        return dict(n=len(available), total_rows=len(rows), unknown_labels=len(rows)-len(available),
                    coverage=len(available)/len(rows), mean_minutes=total/len(available) if available else None,
                    proxy_mae_observed=mean(abs(r["proxy_minutes"]-r["wait_minutes"]) for r in available) if available else None,
                    review_pairs=len(paired), disagreements=conflict,
                    agreement=(len(paired)-conflict)/len(paired) if paired else None)

    m = audit(day)
    available_ids = {r["id"] for r in rows if r["available_day"] is not None and r["available_day"] <= day}
    total = sum(r["wait_minutes"] for r in rows if r["id"] in available_ids)
    reports = dict(available_only=m,
                   zero_fill_demo=dict(n=len(rows), mean_minutes=total/len(rows)),
                   proxy_all=dict(n=len(rows), mean_minutes=mean(r["proxy_minutes"] for r in rows)))
    records = []
    for r in rows:
        visible = r["id"] in available_ids
        reviewed = visible and r["review_minutes"] is not None
        records.append(dict(id=r["id"], period=r["period"], queue_length=r["queue_length"], visible=visible,
                            site=r["site"], day=r["day"], available_day=r["available_day"],
                            record_source=r["record_source"], review_source=r["review_source"],
                            clock_quality=r["clock_quality"],
                            observed_minutes=r["wait_minutes"] if visible else None, proxy_minutes=r["proxy_minutes"],
                            review_minutes=r["review_minutes"] if reviewed else None,
                            proxy_absolute_error=abs(r["proxy_minutes"]-r["wait_minutes"]) if visible else None,
                            review_absolute_difference=abs(r["wait_minutes"]-r["review_minutes"]) if reviewed else None,
                            disagreement=abs(r["wait_minutes"]-r["review_minutes"]) > tolerance if reviewed else None))
    return output("available_only", reports, rows, records, "推迟观察截止日，重新统计实际收到的标签", audit(later),
                  visible_ids=sorted(available_ids), observation_day=day, later_day=later, disagreement_minutes=tolerance,
                  note="填零仅为错误示范；全部代理值的平均不是全部目标值的平均；本课没有调用 AI 标注服务。")


def assign_splits(rows, strategy, config):
    train_end = numeric(config["train_through_day"], "train_through_day", minimum=1, integer=True)
    valid_end = numeric(config["validation_through_day"], "validation_through_day", minimum=train_end+1, integer=True)
    development = [r for r in rows if r["split"] != "test"]
    heldout = [r for r in rows if r["split"] == "test"]
    if strategy == "time":
        if any(r["day"] > valid_end for r in development) or any(r["day"] <= valid_end for r in heldout):
            raise ValueError("时间划分要求开发数据不晚于 validation_through_day，保留测试数据全部在其后。")
        splits = ["train" if r["day"] <= train_end else "validation" for r in development]
        heldout = [{**r, "split": "test"} for r in heldout]
    elif strategy == "group":
        if {r["site"] for r in rows} != {"A", "B", "C"}:
            raise ValueError("分组示例需要 A、B、C 三个窗口；换分组时请一起修改 assign_splits。")
        validation_site = choice(config, "group_validation_site", ("A", "B"))
        train_site = "B" if validation_site == "A" else "A"
        splits = [
            "train" if r["site"] == train_site else
            "validation" if r["site"] == validation_site else
            "unused"
            for r in development
        ]
        heldout = [{**r, "split": "test" if r["site"] == "C" else "unused"} for r in heldout]
    else:
        order = np.random.default_rng(config["seed"]).permutation(len(development))
        splits = ["validation"]*len(development)
        for i in order[:len(development)*2//3]:
            splits[i] = "train"
        heldout = [{**r, "split": "test"} for r in heldout]
    assigned = [{**r, "split": s} for r, s in zip(development, splits)] + heldout
    if any(not any(r["split"] == s for r in assigned) for s in ("train", "validation", "test")):
        raise ValueError("划分后 train、validation、test 都必须有样本；请检查日期或窗口。")
    return assigned


def s03(data, config):
    rows = validate("S03", data, config)
    selected = choice(config, "split_strategy", ("time", "group", "random"))
    reports, records, plans, leakage = {}, [], {}, {}
    for strategy in ("time", "group", "random"):
        assigned = assign_splits(rows, strategy, config)
        train, evaluation = split_rows(assigned, config["evaluation_split"])
        model = fit(train)
        p = predict(model, evaluation)
        # 独立运行一个错误示范：只用结束后小票的分钟数预测实际等待。
        bad_model = fit(train, features=("receipt_minutes",))
        bad = predict(bad_model, evaluation)
        report, trace = regression_reports(evaluation, {strategy: p})
        shared = len({r["site"] for r in train} & {r["site"] for r in evaluation})
        reports[strategy] = {**report[strategy], "train_n": len(train), "shared_sites": shared,
                             "leaked_mae_demo": errors([r["wait_minutes"] for r in evaluation], bad)["mae"]}
        for row, q in zip(trace, bad):
            row["leaked_prediction_demo"] = q
        records.extend(trace)
        plans[strategy] = dict(model=model, train_ids=[r["id"] for r in train],
                               evaluation_ids=[r["id"] for r in evaluation],
                               train_sites=sorted({r["site"] for r in train}),
                               evaluation_sites=sorted({r["site"] for r in evaluation}),
                               test_ids=[r["id"] for r in assigned if r["split"] == "test"],
                               unused_ids=[r["id"] for r in assigned if r["split"] == "unused"])
        leakage[strategy] = errors([r["wait_minutes"] for r in evaluation], bad)
    eval_ids = set(plans[selected]["evaluation_ids"])
    return output(selected, reports, [r for r in rows if r["id"] in eval_ids], records,
                  "在相同划分中误用结束后才知道的小票时间；这是泄漏反例，不是可用方案", leakage[selected],
                  evaluation_split=config["evaluation_split"], splits=plans,
                  note="不同划分的评价样本可能不同，不可按最低 MAE 挑划分；小票字段不得用于真实预测。")


def alert_counts(evaluation, predictions, truth_threshold, alert_threshold, capacity):
    """根据预测排序分配名额；真实标签仅用于最后评价，不参与选择。"""
    if len(predictions) != len(evaluation):
        raise ValueError("每条评价样本必须有一个预测")
    predictions = [numeric(p, "预测分钟数", minimum=None) for p in predictions]
    truth_threshold = numeric(truth_threshold, "long_wait_minutes")
    alert_threshold = numeric(alert_threshold, "alert_threshold")
    capacity = numeric(capacity, "capacity / stress_capacity", integer=True)
    if capacity > len(evaluation):
        raise ValueError("capacity 不能超过当前评价集样本数")
    eligible = [i for i, p in enumerate(predictions) if p >= alert_threshold]
    selected = sorted(eligible, key=lambda i: (-predictions[i], evaluation[i]["id"]))[:capacity]
    flags = [i in selected for i in range(len(evaluation))]
    actual = [r["wait_minutes"] >= truth_threshold for r in evaluation]
    tp = sum(a and b for a, b in zip(flags, actual))
    fp = sum(a and not b for a, b in zip(flags, actual))
    fn = sum(not a and b for a, b in zip(flags, actual))
    tn = sum(not a and not b for a, b in zip(flags, actual))
    return dict(alerts=len(selected), eligible=len(eligible), tp=tp, fp=fp, fn=fn, tn=tn), flags


def s04(data, config):
    rows = validate("S04", data, config)
    primary = choice(config, "primary_model", ("baseline", "linear", "buffered"))
    weight = numeric(config["underestimate_weight"], "underestimate_weight", minimum=1)
    buffer = numeric(config["buffer_minutes"], "buffer_minutes")
    truth_threshold = numeric(config["long_wait_minutes"], "long_wait_minutes")
    alert_threshold = numeric(config["alert_threshold"], "alert_threshold")
    train, evaluation = split_rows(rows, config["evaluation_split"])
    model = fit(train)
    linear = predict(model, evaluation)
    ps = dict(baseline=[mean(r["wait_minutes"] for r in train)]*len(evaluation),
              linear=linear, buffered=[p+buffer for p in linear])
    reports, records = regression_reports(evaluation, ps, weight)
    decisions = {}
    for name, p in ps.items():
        counts, flags = alert_counts(evaluation, p, truth_threshold, alert_threshold, config["capacity"])
        reports[name].update(counts)
        decisions[name] = flags
    indices = {r["id"]: i for i, r in enumerate(evaluation)}
    for r in records:
        r["long_wait"] = r["actual"] >= truth_threshold
        r["alert"] = decisions[r["method"]][indices[r["id"]]]
        r["weighted_error"] = (r["actual"]-r["prediction"])*weight if r["prediction"] < r["actual"] else r["prediction"]-r["actual"]
    stress = {name: alert_counts(evaluation, p, truth_threshold, alert_threshold, config["stress_capacity"])[0]
              for name, p in ps.items()}
    return output(primary, reports, evaluation, records, "预测保持不变，只改变可用提醒名额", stress,
                  evaluation_split=config["evaluation_split"], model=model, by_period=grouped(evaluation, ps),
                  note="阈值单位是分钟，不是概率；缓冲不改变已拟合的回归参数；分数不自动决定采用方案。")


def choose_pool(pool, budget, strategy, period, seed):
    """仅根据可用信息选样本；不读取候选标签，也不读取验证集/测试集。"""
    if strategy == "random_sample":
        indices = np.random.default_rng(seed).choice(len(pool), budget, replace=False)
        return [pool[int(i)] for i in indices]
    return sorted(pool, key=lambda r: (r["period"] != period, r["id"]))[:budget]


def s05(data, config):
    rows = validate("S05", data, config)
    primary = choice(config, "primary_strategy", ("no_addition", "random_sample", "group_first", "synthetic"))
    period = choice(config, "target_period", ("午间", "晚间"))
    stress_period = choice(config, "stress_period", ("午间", "晚间"))
    offset = numeric(config["synthetic_offset"], "synthetic_offset", minimum=None)
    budget = numeric(config["budget"], "budget", minimum=1, integer=True)
    train, evaluation = split_rows(rows, config["evaluation_split"])
    pool = [r for r in rows if r["split"] == "pool"]
    if budget > len(pool):
        raise ValueError("budget 不能超过 pool 候选池的样本数")
    original = fit(train)
    synth = []
    for i in range(budget):
        r = {**train[i % len(train)], "id": f"synthetic-{i+1}", "split": "train"}
        r["wait_minutes"] = predict(original, [r])[0] + offset
        if r["wait_minutes"] < 0:
            raise ValueError("synthetic_offset 使生成标签为负；请改用合理的分钟数")
        synth.append(r)
    additions = dict(no_addition=[],
                     random_sample=choose_pool(pool, budget, "random_sample", period, config["seed"]),
                     group_first=choose_pool(pool, budget, "group_first", period, config["seed"]), synthetic=synth)
    models = {name: fit(train+added) for name, added in additions.items()}
    predictions = {name: predict(model, evaluation) for name, model in models.items()}
    reports, records = regression_reports(evaluation, predictions)
    added_records = []
    for name, added in additions.items():
        reports[name].update(train_n=len(train)+len(added), added_n=len(added),
                             evening_train_n=sum(r["period"] == "晚间" for r in train+added))
        for r in added:
            added_records.append(dict(method=name, id=r["id"], period=r["period"], queue_length=r["queue_length"],
                                      label=r["wait_minutes"], label_source="模型生成（模拟）" if name == "synthetic" else "候选池观察标签（人工教学数据）"))
    stress_add = choose_pool(pool, budget, "group_first", stress_period, config["seed"])
    stress = errors([r["wait_minutes"] for r in evaluation], predict(fit(train+stress_add), evaluation))
    result = output(primary, reports, evaluation, records, "预算不变，改为优先补另一时段的样本", stress,
                    evaluation_split=config["evaluation_split"], models=models,
                    selected_ids={k: [r["id"] for r in v] for k, v in additions.items()},
                    by_period=grouped(evaluation, predictions), stress_selected_ids=[r["id"] for r in stress_add],
                    note="全部数据均人工构造；pool 模拟采集，synthetic 模拟自动生成标签，不是实际 AI 标注实验。")
    result["details"]["tables"]["added_samples"] = added_records
    return result


def s06(data, config):
    rows = validate("S06", data, config)
    change = choice(config, "change", ("imputation", "period_feature"))
    shift = numeric(config["stress_queue_shift"], "stress_queue_shift", integer=True)
    train, evaluation = split_rows(rows, config["evaluation_split"])
    models = dict(original=fit(train, imputation="zero"),
                  candidate=fit(train, imputation="mean") if change == "imputation"
                  else fit(train, features=("queue_length", "evening"), imputation="zero"))
    ps = {k: predict(m, evaluation) for k, m in models.items()}
    reports, records = regression_reports(evaluation, ps)
    for k, m in models.items():
        reports[k]["train_mae"] = errors([r["wait_minutes"] for r in train], predict(m, train))["mae"]
    for r in records:
        r["queue_missing"] = r["queue_length"] is None
        r["queue_after_imputation"] = models[r["method"]]["fill_value"] if r["queue_missing"] else r["queue_length"]
    changed = deepcopy(evaluation)
    for r in changed:
        if r["queue_length"] is not None:
            r["queue_length"] += shift
    stress = {k: errors([r["wait_minutes"] for r in changed], predict(m, changed)) for k, m in models.items()}
    by_missing = {}
    for missing in (False, True):
        idx = [i for i, r in enumerate(evaluation) if (r["queue_length"] is None) == missing]
        if idx:
            by_missing["missing" if missing else "known"] = {k: errors([evaluation[i]["wait_minutes"] for i in idx], [p[i] for i in idx]) for k, p in ps.items()}
    return output("candidate", reports, evaluation, records,
                  "模型不重训，已知人数统一加上指定值，真实等待保持原值，模拟记录错误", stress,
                  evaluation_split=config["evaluation_split"], models=models, change=change,
                  by_period=grouped(evaluation, ps), by_missing=by_missing,
                  changed_factor="人数填补：0 → 训练集均值" if change == "imputation" else "特征：增加晚间指示变量；填补仍为 0",
                  note="先在本课同一数据版本上重跑原方案，再比较候选；不能直接拿 S01 的旧分数作差。")


EXPERIMENTS = {f"S{i:02d}": globals()[f"s{i:02d}"] for i in range(1, 7)}


def label_audit_console_summary(result):
    """S02 只展示标签统计；配对规则改变时让学生能看到变化。"""
    d, m = result["details"], result["metrics"]
    def number(value):
        return "未定义" if value is None else f"{value:.6g}"
    agreement = "未定义（没有配对）" if m["agreement"] is None else f"{100*m['agreement']:.6g}%"
    later = result["stress_test"]["metrics"]
    return "\n".join([
        f"S02 标签检查：固定 {m['total_rows']} 条已发生记录；主截止日为第 {d['observation_day']} 天结束。",
        f"已收到 {m['n']}/{m['total_rows']} 条；标签覆盖率 {100*m['coverage']:.6g}%；未知 {m['unknown_labels']} 条。",
        f"已知标签均值 = {number(m['mean_minutes'])} 分钟；均值分母为 {m['n']}，不是全部记录数。",
        f"直接观测值和独立复核值可比较 {m['review_pairs']} 对；差异 > {d['disagreement_minutes']:.6g} 分钟才标记为分歧，标注者间分歧 {m['disagreements']} 对；一致比例 {agreement}（标注者间一致性比例）。",
        f"代理值 MAE = {number(m['proxy_mae_observed'])} 分钟，只比较当前已收到直接观测目标值的记录。",
        "填零是错误示范；全部代理值的均值不是全部目标值的均值。先从生成的 records.csv 核对一行，再读 comparison.csv。",
        f"额外截止日第 {d['later_day']} 天：已收到 {later['n']}/{later['total_rows']} 条；已知均值 {number(later['mean_minutes'])} 分钟。",
        "日期控制哪些直接观测标签可见；分歧容差只改变复核标记，不修改原值。没有配对不等于全部正确；本课没有调用 AI 服务。",
    ])


def console_summary(result):
    """给初学者的最小结果导航，不代写结论。"""
    d = result["details"]
    if result.get("lesson") in {"S01", "lesson-03"}:
        split = {"validation": "验证集", "test": "测试集"}[d["evaluation_split"]]
        lines = [f"S01：训练样本 {len(d['train_ids'])} 条；{split} {len(d['evaluation_ids'])} 条。",
                 "比较结果（不是自动推荐）：MAE 单位为分钟，提醒依据预测值。"]
        for row in d["tables"]["comparison"]:
            value = "未定义" if row["mae"] is None else f"{row['mae']:.6g}"
            lines.append(f"{row['method_name']}；样本数={row['n']}；MAE/分钟={value}；提醒数={row['alerts']}")
        lines.append("alert: True=提醒，False=不提醒；MAE 空白或 null 不是 0。")
        stress = result["stress_test"]["metrics"]
        values = "；".join(f"{NAMES[name]}={value:.6g} 分钟"
                          for name, value in stress["predictions"].items())
        lines.append(f"新输入检查：{stress['queue_length']} 人；{values}。没有标签，不能计算误差。")
        lines.append("这个新输入没有加入验证/测试集，不改变比较表中的样本数或 MAE。")
        lines.append("先从 records.csv 找指定方法的一行，再读 comparison.csv；其他指标按需查数据说明。")
        lines.append(d["note"])
        return "\n".join(lines)
    if d.get("primary_method") == "available_only":
        return label_audit_console_summary(result)
    if result.get("lesson") in {"S03", "lesson-05"}:
        lines = ["第 05 课数据划分结果（不是自动推荐）："]
        for row in d["tables"]["comparison"]:
            lines.append(
                f"{row['method_name']}；训练集 {row['train_n']} 条；"
                f"验证集 {row['n']} 条；训练集和验证集共有取餐窗口 {row['shared_sites']} 个；"
                f"验证集 MAE = {row['mae']:.6g} 分钟"
            )
        lines += [
            "先根据将来的使用对象选择划分方法，再比较对应记录上的 MAE；三行使用的验证记录并不相同。",
            "请先打开 comparison.csv 核对分母，再到 summary.json 的 details.splits 中核对训练和验证编号。",
            "leaked_mae_demo 是误用结束后小票时间得到的目标泄漏反例，不能作为候选方案。",
        ]
        return "\n".join(lines)
    lines = ["比较结果（不是自动推荐）："]
    for r in d["tables"]["comparison"]:
        parts = [r["method_name"]]
        for key, label in (("n", "评价样本数"), ("mae", "MAE/分钟"), ("asymmetric_loss", "加权误差"),
                           ("mean_minutes", "平均分钟数"), ("coverage", "标签覆盖率"),
                           ("alerts", "提醒数"), ("fp", "误报"), ("fn", "漏报"), ("train_n", "训练样本数")):
            if key in r:
                value = "未定义" if r[key] is None else f"{r[key]:.6g}"
                parts.append(f"{label}={value}")
        lines.append("；".join(parts))
    if "by_period" in d:
        lines.append("按时段核对（分组数量小，不能直接推广到真实人群）：")
        for period, methods in d["by_period"].items():
            for name, metric in methods.items():
                lines.append(f"{period}；{NAMES.get(name, name)}；样本数={metric['n']}；MAE={metric['mae']:.6g} 分钟")
    lines += ["先看 comparison.csv 对应方法和分母，再从 records.csv 找一条样本核对。",
              d.get("note", "这是人工数据实验，不是实际使用效果的证明。")]
    return "\n".join(lines)
