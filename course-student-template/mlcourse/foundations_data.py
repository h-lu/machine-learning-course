"""S01–S06 的人工教学数据。数值用于解释机制，不代表真实食堂或 AI 的表现。"""
from __future__ import annotations

from copy import deepcopy

TITLES = {
    "S01": "怎样把模糊需求变成可研究的问题",
    "S02": "这份数据和标签代表谁、代表什么",
    "S03": "怎样比较才接近未来使用",
    "S04": "什么算做好了，失败会造成什么后果",
    "S05": "还缺哪些数据，哪些记录值得补",
    "S06": "一次小实验能否改变最初的问题",
}
CONFIGS = {
    "S01": dict(seed=7, evaluation_split="validation", primary_model="linear",
                rule_intercept=1.0, rule_slope=2.0, alert_minutes=8.0, stress_queue=10),
    "S02": dict(seed=7, observation_day=4, later_day=7, disagreement_minutes=2.0),
    "S03": dict(seed=7, evaluation_split="validation", split_strategy="time",
                train_through_day=4, validation_through_day=6),
    "S04": dict(seed=7, evaluation_split="validation", primary_model="linear",
                buffer_minutes=4.0, underestimate_weight=3.0,
                long_wait_minutes=8.0, alert_threshold=8.0, capacity=2, stress_capacity=1),
    "S05": dict(seed=7, evaluation_split="validation", budget=4,
                target_period="晚间", primary_strategy="group_first",
                synthetic_offset=0.0, stress_period="午间"),
    "S06": dict(seed=7, evaluation_split="validation", change="imputation", stress_queue_shift=3),
}


def core_rows() -> list[dict]:
    """3 个虚构窗口，每个窗口 8 天；前 4 天训练，5–6 天验证，7–8 天测试。"""
    rows = []
    for index, site in enumerate(("A", "B", "C")):
        for day in range(1, 9):
            queue = (day - 1 + index) % 4
            period = "午间" if site == "A" else "晚间"
            # 不同窗口和日期的差异是人为设置的，用于讨论模型遗漏信息。
            wait = 1 + 2 * queue + (0, 4, 6)[index] + (1 if day >= 5 else 0)
            rows.append(dict(id=f"{site}{day:02d}", queue_length=queue,
                             wait_minutes=wait, period=period, site=site, day=day,
                             staff_count=((day + index) % 3) + 1,
                             weather=("雨" if day in (3, 6) else "晴" if day % 2 else "阴"),
                             event_flag=day in (3, 6),
                             split="train" if day <= 4 else "validation" if day <= 6 else "test"))
    return rows


def example_config(lesson: str) -> dict:
    if lesson not in CONFIGS:
        raise ValueError("本模块只支持 S01–S06")
    return deepcopy(CONFIGS[lesson])


def example_data(lesson: str) -> dict:
    if lesson not in TITLES:
        raise ValueError("本模块只支持 S01–S06")
    rows = core_rows()
    kind = "foundation_waiting"
    note = "S01/S03/S04 共用 24 条样本；S06 只隐藏其中部分人数，不改变标签。"
    if lesson == "S02":
        kind = "foundation_label_audit"
        rows = [r for r in rows if r["site"] in {"A", "B"} and r["day"] <= 4]
        for r, available in zip(rows, [1, 2, 6, 4, 5, 3, 7, None]):
            r.pop("split")
            r["available_day"] = available
            r["proxy_minutes"] = 1 + 2 * r["queue_length"]
            r["review_minutes"] = r["wait_minutes"] + (3 if r["id"] == "A04" else 0)
            r["record_source"] = ["直接计时", "直接计时", "日志重建", "直接计时",
                                   "日志重建", "直接计时", "日志重建", "未提供"][len(rows) - 8]
            r["review_source"] = None if r["id"] == "B04" else "第二人复核"
            r["clock_quality"] = ["完整", "完整", "缺开始时间", "完整",
                                   "完整", "完整", "缺结束备注", "缺失"][len(rows) - 8]
            if available is None:
                r["wait_minutes"] = r["review_minutes"] = None
        note = "available_day 是记录上传日期，不是等待了几天；代理值和复核值均人工编写，不是实际 AI 输出。"
    elif lesson == "S03":
        for r in rows:
            # 三种训练/验证划分只使用开发部分；原 test 行始终单独保留。
            r["receipt_minutes"] = r["wait_minutes"] + 0.25
        note = "receipt_minutes 是结束后小票才有的时间，仅供演示数据泄漏，不能作正常预测特征。"
    elif lesson == "S05":
        kind = "foundation_sampling"
        for r in rows:
            if r["split"] == "train" and r["period"] == "晚间":
                r["split"] = "pool"
        rows.extend(dict(id=f"extra-A{i+1}", queue_length=q, wait_minutes=1+2*q,
                         period="午间", site="A", day=3, split="pool")
                    for i, q in enumerate([0, 1, 2, 3]))
        note = "初始训练集只有 4 条午间样本；候选池 12 条。选择只读人数、时段和编号，选中后才取标签。全部仍为人工数据。"
    elif lesson == "S06":
        missing = {"A02", "B03", "C04", "A05", "B06", "C07"}
        for r in rows:
            if r["id"] in missing:
                r["queue_length"] = None
        note += " 隐藏 A02/B03/C04/A05/B06/C07 的人数；没有在输入中保留被隐藏的数值。"
    return dict(kind=kind, source={"type": "synthetic", "generator": "mlcourse/foundations_data.py",
                                  "limitation": "人工教学数据，不代表真实人群、因果效果或 AI 能力。", "note": note},
                rows=rows)
