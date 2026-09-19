"""独立核对 S01–S06 的数据、数值与比较条件；不判断学生应选哪种方案。"""
from statistics import mean
import math
import numpy as np


def near(a, b, message, tolerance=1e-7):
    if not math.isfinite(a) or abs(a-b) > tolerance:
        raise AssertionError(f"{message}: {a} != {b}")


def line(rows):
    """不调用学生拟合函数，使用一元最小二乘的显式求和公式。"""
    x = [r["queue_length"] for r in rows]; y = [r["wait_minutes"] for r in rows]
    xb, yb = mean(x), mean(y)
    slope = sum((a-xb)*(b-yb) for a,b in zip(x,y))/sum((a-xb)**2 for a in x)
    return yb-slope*xb, slope


def verify(lesson, data, config, result):
    rows = data["rows"]; by_id = {r["id"]: r for r in rows}
    detail = result["details"]; records=detail["tables"]["records"]
    reports={detail["primary_method"]: result["metrics"], **result["comparison"]}
    checks=[]
    # Recompute every displayed method's error from individual records, not the algorithm output score.
    if lesson != "S02":
        for method, report in reports.items():
            if method == "no_action":
                if report["mae"] is not None: raise AssertionError("没有分钟预测不应声称 MAE 为零")
                continue
            selected=[r for r in records if r["method"]==method]
            if len(selected)!=report["n"]: raise AssertionError("评价分母不匹配")
            for r in selected:
                near(r["actual"], by_id[r["id"]]["wait_minutes"], "实际标签来自原数据")
                near(r["absolute_error"], abs(r["prediction"]-r["actual"]), "逐条绝对误差")
            near(report["mae"], mean(r["absolute_error"] for r in selected), "MAE 独立重算")
            near(report["rmse"], math.sqrt(mean(r["absolute_error"]**2 for r in selected)), "RMSE 独立重算")
        checks.append("逐条真实标签和预测独立重算全部方法的误差与分母")
    if lesson == "S01":
        train=[r for r in rows if r["split"]=="train"]
        a,b=line(train)
        for r in records:
            x=by_id[r["id"]]["queue_length"]
            p={"linear":a+b*x,"rule":config["rule_intercept"]+config["rule_slope"]*x,
               "baseline":mean(r["wait_minutes"] for r in train)}[r["method"]]
            near(r["prediction"],p,"规则、均值及线性解")
            if r["alert"] != (p>=config["alert_minutes"]): raise AssertionError("提醒条件不一致")
        if detail["intervention_effect"] is not None: raise AssertionError("无干预数据不应预填因果效果")
        checks.append("用显式公式核对三种预测、阈值和无因果效果声明")
    elif lesson == "S02":
        visible=[r for r in rows if r["available_day"] is not None and r["available_day"]<=config["observation_day"]]
        m=result["metrics"]
        if len(visible)!=m["n"] or len(rows)-len(visible)!=m["unknown_labels"]: raise AssertionError("截止日期统计错误")
        near(m["coverage"],len(visible)/len(rows),"标签覆盖率")
        near(m["mean_minutes"],mean(r["wait_minutes"] for r in visible),"已知标签均值")
        near(result["comparison"]["zero_fill_demo"]["mean_minutes"],sum(r["wait_minutes"] for r in visible)/len(rows),"填零反例")
        visible_ids={r["id"] for r in visible}
        for r in records:
            if r["id"] not in visible_ids and r["observed_minutes"] is not None: raise AssertionError("提前公开未知标签")
        paired=[r for r in visible if r["review_minutes"] is not None]
        expected=sum(abs(r["wait_minutes"]-r["review_minutes"])>config["disagreement_minutes"] for r in paired)
        if expected!=m["disagreements"]:raise AssertionError("分歧计数错误")
        checks += ["直接扫描截止日期、覆盖率和未知标签掩码", "按原数据核对两种分母、代理标签与复核分歧"]
    elif lesson == "S03":
        reserved={r["id"] for r in rows if r["split"]=="test"}
        for strategy,plan in detail["splits"].items():
            tr=set(plan["train_ids"]); ev=set(plan["evaluation_ids"])
            if tr & ev or tr & reserved:raise AssertionError("训练集使用了评价或保留测试行")
            if config["evaluation_split"]=="validation" and ev & reserved:raise AssertionError("测试用于划分选择")
            if strategy=="time" and max(by_id[i]["day"] for i in tr)>=min(by_id[i]["day"] for i in ev):raise AssertionError("时间顺序错误")
            if strategy=="group" and {by_id[i]["site"] for i in tr}&{by_id[i]["site"] for i in ev}:raise AssertionError("窗口泄漏")
            a,b=line([by_id[i] for i in plan["train_ids"]])
            for r in records:
                if r["method"]==strategy:near(r["prediction"],a+b*by_id[r["id"]]["queue_length"],"正常划分预测")
            near(reports[strategy]["leaked_mae_demo"],0,"人工小票关系应暴露虚假低误差")
        checks += ["检查所有划分都保留原测试行、时间顺序与对象分离", "独立线性解及事后小票泄漏反例"]
    elif lesson == "S04":
        for method, report in reports.items():
            rs=[r for r in records if r["method"]==method]
            expected=mean((r["actual"]-r["prediction"])*config["underestimate_weight"] if r["prediction"]<r["actual"] else r["prediction"]-r["actual"] for r in rs)
            near(report["asymmetric_loss"],expected,"非对称损失")
            selected=sorted([r for r in rs if r["prediction"]>=config["alert_threshold"]],key=lambda r:(-r["prediction"],r["id"]))[:config["capacity"]]
            ids={r["id"] for r in selected}
            for k,a,b in [("tp",True,True),("fp",True,False),("fn",False,True),("tn",False,False)]:
                n=sum((r["id"] in ids)==a and (r["actual"]>=config["long_wait_minutes"])==b for r in rs)
                if n!=report[k]:raise AssertionError(f"{k}计数不符")
            if report["alerts"]!=len(ids):raise AssertionError("容量不符")
        checks += ["逐条低估权重及独立排序核对容量、四类计数"]
    elif lesson == "S05":
        train=[r for r in rows if r["split"]=="train"]
        pool={r["id"] for r in rows if r["split"]=="pool"}
        for method,model in detail["models"].items():
            added=[r for r in detail["tables"]["added_samples"] if r["method"]==method]
            if method!="no_addition" and len(added)!=config["budget"]:raise AssertionError("新增预算不同")
            if len({r["id"] for r in added})!=len(added):raise AssertionError("重复采样")
            if method not in {"synthetic","no_addition"} and not {r["id"] for r in added}<=pool:raise AssertionError("候选超出 pool")
            extra=[dict(queue_length=r["queue_length"],wait_minutes=r["label"]) for r in added]
            a,b=line(train+extra)
            for r in records:
                if r["method"]==method:near(r["prediction"],a+b*by_id[r["id"]]["queue_length"],"补数据后独立拟合")
        checks += ["新增预算、唯一编号与候选池界限", "对实际入选标签用显式公式重算拟合结果"]
    elif lesson == "S06":
        train=[r for r in rows if r["split"]=="train"]
        for name,model in detail["models"].items():
            expected=mean(r["queue_length"] for r in train if r["queue_length"] is not None) if model["imputation"]=="mean" else 0
            near(model["fill_value"],expected,"只从训练行填补")
            x=np.asarray([[1, expected if r["queue_length"] is None else r["queue_length"]]+([int(r["period"]=="晚间")] if "evening" in model["features"] else []) for r in train],dtype=float)
            y=np.asarray([r["wait_minutes"] for r in train])
            w=np.linalg.solve(x.T@x,x.T@y)
            np.testing.assert_allclose(w,model["coefficients"],atol=1e-7)
        old,new=detail["models"]["original"],detail["models"]["candidate"]
        if config["change"]=="imputation" and old["features"]!=new["features"]:raise AssertionError("填补实验误改特征")
        if config["change"]=="period_feature" and old["fill_value"]!=new["fill_value"]:raise AssertionError("特征实验误改填补")
        checks += ["训练集填补值与另一线性代数入口核对系数", "明确只改变一个因素，保留原方案和候选"]
    if not checks:raise AssertionError("没有实际独立检查")
    return checks
