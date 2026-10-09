from pathlib import Path
import json

import shutil, subprocess, sys, tempfile
# Teacher-side independent student-path simulation; only the disposable copy is edited.
PROJECT = Path(__file__).resolve().parents[2]
_scratch = tempfile.TemporaryDirectory(prefix="ml-student-coldread-")
ROOT = Path(_scratch.name) / "student"
shutil.copytree(PROJECT / "course-student-template", ROOT, ignore=shutil.ignore_patterns("__pycache__", "artifacts", ".git"))
COMMANDS = []
def command(args):
    result = subprocess.run([sys.executable, "scripts/course.py", *args], cwd=ROOT, capture_output=True, text=True)
    COMMANDS.append({"command":"python3 scripts/course.py " + " ".join(args), "exit_code":result.returncode})
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
for number in range(4, 8):
    command(["run", f"{number:02d}"])
    starter = ROOT / f"lesson-{number:02d}" / "artifacts/starter"
    assert json.loads((starter / "summary.json").read_text())["status"] == "not_started"
    assert not (starter / "records.csv").exists()

COMMON = '''from pathlib import Path
import sys, json, csv, random
from collections import Counter, defaultdict
from datetime import datetime, timedelta
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mlcourse.bike_starter import load_development, write_csv, mae
HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "my-config.json").read_text())
OUT = HERE / "artifacts" / "personal"
OUT.mkdir(parents=True, exist_ok=True)
def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\\n")
def table(name, rows):
    write_csv(OUT / name, rows)
def model(rows):
    groups=defaultdict(list)
    for row in rows: groups[(row["hr"], row["workingday"])].append(row["cnt"])
    fallback=sum(row["cnt"] for row in rows)/len(rows)
    means={key: sum(values)/len(values) for key, values in groups.items()}
    return means, fallback
def predict(fitted, row):
    means, fallback=fitted
    return means.get((row["hr"], row["workingday"]), fallback)
def commute(row):
    return row["workingday"] == 1 and row["hr"] in (7,8,9,16,17,18,19)
'''

FOUR = '''# Read only clock metadata from the official file; do not parse sealed targets.
with (ROOT / "data/bike/hour.csv").open(newline="") as stream:
    observed={datetime.fromisoformat(row["dteday"])+timedelta(hours=int(row["hr"]))
              for row in csv.DictReader(stream)}
start=datetime.fromisoformat(CFG["start"]); end=datetime.fromisoformat(CFG["end"])
expected=[]; t=start
while t<end: expected.append(t); t+=timedelta(hours=1)
rows=[]
for hr in range(24):
    clock=[t for t in expected if t.hour==hr]
    count=sum(t in observed for t in clock)
    rows.append({"hr":hr,"expected":len(clock),"observed":count,"missing":len(clock)-count,"coverage":count/len(clock)})
table("coverage.csv", rows)
missing=[{"datetime":t.isoformat(timespec="minutes"),"hr":t.hour} for t in expected if t not in observed]
table("missing.csv",missing)
with (HERE/"data/label-source-demo.csv").open(newline="") as stream: demo=list(csv.DictReader(stream))
reviews=[]
for tolerance in CFG["tolerances"]:
    for row in demo:
        review=None if not row["review_minutes"] else float(row["review_minutes"])
        reviews.append({"id":row["id"],"tolerance":tolerance,"direct":float(row["direct_minutes"]),"proxy":float(row["proxy_minutes"]),"review":review,"needs_review":review is None or abs(review-float(row["direct_minutes"]))>tolerance})
table("simulated_review.csv",reviews)
groups={}
for name,hours in CFG["hour_groups"].items():
    selected=[row for row in rows if row["hr"] in hours]
    n=sum(row["expected"] for row in selected); k=sum(row["observed"] for row in selected)
    groups[name]={"expected":n,"observed":k,"missing":n-k,"coverage":k/n}
save("summary.json", {"groups":groups,"overall_expected":len(expected),"overall_observed":len(expected)-len(missing),"simulated_delay":{"known_day2_mean":4,"known_day5_mean":10,"INVALID_zero_filled_day2_mean":2},"target_statistics_read":False,"source_demo":"artificial, not Bike independent review"})
'''

FIVE = '''train,val,audit=load_development(ROOT); development=train+val
days=sorted({r["dteday"] for r in development}); rng=random.Random(CFG["seed"])
held=set(rng.sample(days,CFG["random_days"]))
row_held=set(random.Random(CFG["seed"]).sample([r["instant"] for r in development],len(val)))
schemes={"time":(train,val),"random_day":([r for r in development if r["dteday"] not in held],[r for r in development if r["dteday"] in held]),"random_row":([r for r in development if r["instant"] not in row_held],[r for r in development if r["instant"] in row_held])}
records=[]; roles=[]; models=[]; metrics={}
for name,(tr,va) in schemes.items():
    fitted=model(tr); guesses=[predict(fitted,r) for r in va]; truth=[r["cnt"] for r in va]
    metrics[name]={"training_rows":len(tr),"validation_rows":len(va),"training_mean":fitted[1],"group_mean_mae":mae(truth,guesses),"global_mean_mae":mae(truth,[fitted[1]]*len(va)),"overlapping_days":len({r["dteday"] for r in tr}&{r["dteday"] for r in va})}
    for r,p in zip(va,guesses): records.append({"scheme":name,"instant":r["instant"],"datetime":r["datetime"],"actual":r["cnt"],"prediction":p,"absolute_error":abs(r["cnt"]-p)})
    for role,part in (("train",tr),("validation",va)):
        roles.extend({"scheme":name,"instant":r["instant"],"date":r["dteday"],"role":role} for r in part)
    for (hr,workingday),mean in sorted(fitted[0].items()): models.append({"scheme":name,"hr":hr,"workingday":workingday,"training_mean":mean,"count":sum(r["hr"]==hr and r["workingday"]==workingday for r in tr)})
assert metrics["time"]["overlapping_days"]==metrics["random_day"]["overlapping_days"]==0
assert all(r["dteday"] < "2012-10-01" for r in development)
table("records.csv",records); table("roles.csv",roles); table("model.csv",models)
save("summary.json",{"schemes":metrics,"sealed_targets_used":False,"selected_for_later_dates":"time","group_unit":"day; not station or person"})
save("INVALID_target_parts.json",{"valid_model":False,"input":"casual+registered","identity_holds":all(r["casual"]+r["registered"]==r["cnt"] for r in val),"excluded_from_comparison":True})
'''

SIX = '''train,val,audit=load_development(ROOT); fitted=model(train)
base=[]; daily=defaultdict(list)
for r in val:
    p=predict(fitted,r); e=p-r["cnt"]
    row={"instant":r["instant"],"datetime":r["datetime"],"date":r["dteday"],"hr":r["hr"],"workingday":r["workingday"],"actual":r["cnt"],"prediction":p,"absolute_error":abs(e),"weighted_error":abs(e)*(CFG["underweight"] if e<0 else 1),"candidate":p>=CFG["threshold"],"actual_high":r["cnt"]>=CFG["threshold"]}
    base.append(row); daily[row["date"]].append(row)
results=[]; capacity_rows=[]; metrics={}
for cap in CFG["capacities"]:
    selected=set()
    for date,batch in sorted(daily.items()):
        candidates=sorted([r for r in batch if r["candidate"]],key=lambda r:(-r["prediction"],r["datetime"]))
        chosen=candidates[:cap]; selected.update(r["instant"] for r in chosen)
        capacity_rows.append({"capacity":cap,"date":date,"candidates":len(candidates),"selected":len(chosen)})
    counts=Counter()
    for row in base:
        final=row["instant"] in selected; high=row["actual_high"]
        outcome="TP" if final and high else "FP" if final else "FN" if high else "TN"
        counts[outcome]+=1; results.append({"capacity":cap,**row,"final_alert":final,"outcome":outcome})
    precision=counts["TP"]/(counts["TP"]+counts["FP"]) if selected else None
    recall=counts["TP"]/(counts["TP"]+counts["FN"])
    metrics[str(cap)]={"rows":len(base),"mae":sum(r["absolute_error"] for r in base)/len(base),"weighted_mae":sum(r["weighted_error"] for r in base)/len(base),"confusion":dict(counts),"precision":precision,"recall":recall,"selected":len(selected)}
assert metrics["0"]["precision"] is None
assert metrics["2"]["mae"]==metrics["5"]["mae"]
assert all(r["selected"]<=r["capacity"] and r["selected"]<=r["candidates"] for r in capacity_rows)
table("records.csv",results);table("daily_capacity.csv",capacity_rows)
slice_rows=[r for r in base if r["workingday"]==1 and r["hr"] in (7,8,9,16,17,18,19)]
save("summary.json",{"capacities":metrics,"threshold":CFG["threshold"],"underweight":CFG["underweight"],"commute_rows":len(slice_rows),"commute_mae":sum(r["absolute_error"] for r in slice_rows)/len(slice_rows),"evaluation":"same-hour offline daily batches, no causal or realtime claim"})
'''

SEVEN = '''train,val,audit=load_development(ROOT); by_id={r["instant"]:r for r in train}
# Only these fields are passed to selection; labels stay outside this view.
visible=[{k:r[k] for k in ("instant","dteday","hr","workingday","weathersit")} for r in train]
plans=[]; metrics=[]; predictions=[]; synthetic=[]
for seed in CFG["seeds"]:
    rng=random.Random(seed); ids=[r["instant"] for r in visible]; initial=set(rng.sample(ids,CFG["initial"]))
    pool=[r for r in visible if r["instant"] not in initial]
    counts=Counter((r["hr"],r["workingday"]) for r in visible if r["instant"] in initial)
    random_ids=random.Random(seed+1000).sample([r["instant"] for r in pool],CFG["budget"])
    shuffled=list(pool); random.Random(seed+2000).shuffle(shuffled)
    focus_ids=[r["instant"] for r in sorted(shuffled,key=lambda r:(not commute(r),counts[(r["hr"],r["workingday"])]))[:CFG["budget"]]]
    for strategy,chosen in (("random",random_ids),("commute_focus",focus_ids)):
        plans.extend({"seed":seed,"strategy":strategy,"role":"initial",**r} for r in visible if r["instant"] in initial)
        plans.extend({"seed":seed,"strategy":strategy,"role":"selected",**r} for r in pool if r["instant"] in chosen)
    # Persist label-free IDs and reasons before fitting any seed's model.
    table("selection_without_labels.csv",plans)
    save("plan.json",{"config":CFG,"source":"existing real training records, simulated annotation budget","features_for_selection":["instant","dteday","hr","workingday","weathersit"],"strategies":["random","commute_focus"],"labels_passed_to_selection":False})
    initial_rows=[by_id[i] for i in sorted(initial)]; initial_model=model(initial_rows)
    for strategy,chosen in (("initial",[]),("random",random_ids),("commute_focus",focus_ids)):
        assert not initial.intersection(chosen) and len(chosen)==len(set(chosen))
        fitted=model(initial_rows+[by_id[i] for i in chosen]); guesses=[predict(fitted,r) for r in val]
        subset=[(r,p) for r,p in zip(val,guesses) if commute(r)]
        metrics.append({"seed":seed,"strategy":strategy,"real_labels":len(initial)+len(chosen),"validation_rows":len(val),"mae":mae([r["cnt"] for r in val],guesses),"commute_rows":len(subset),"commute_mae":mae([r["cnt"] for r,p in subset],[p for r,p in subset]),"covered_groups":len(fitted[0])})
        predictions.extend({"seed":seed,"strategy":strategy,"instant":r["instant"],"actual":r["cnt"],"prediction":p} for r,p in zip(val,guesses))
    # Model-produced labels on repeated inputs add no independent observation.
    pseudo=[{**r,"cnt":predict(initial_model,r)} for r in initial_rows[:CFG["budget"]]]
    pseudo_model=model(initial_rows+pseudo)
    synthetic.append({"seed":seed,"generated_rows":len(pseudo),"new_independent_labels":0,"max_prediction_change":max(abs(predict(pseudo_model,r)-predict(initial_model,r)) for r in val),"source":"rule-generated labels from initial model; not an actual AI API call"})
table("metrics.csv",metrics);table("records.csv",predictions)
save("summary.json",{"metrics":metrics,"synthetic_control":synthetic,"weather4_train_rows":sum(r["weathersit"]==4 for r in train),"weather4_validation_rows":sum(r["weathersit"]==4 for r in val),"all_seeds_reported":True,"sealed_test_used":False})
'''

configs = {
  4:{"start":"2011-01-01","end":"2011-04-01","hour_groups":{"early_morning":[2,3,4,5,6],"morning_commute":[7,8,9]},"tolerances":[2,4]},
  5:{"seed":29,"random_days":92,"method":"hour_workingday_mean","use":"later calendar dates"},
  6:{"underweight":3,"threshold":350,"capacities":[2,5,0],"method":"hour_workingday_mean"},
  7:{"seeds":[11,23,37],"initial":240,"budget":96,"use":"commute estimation","method":"hour_workingday_mean"},
}
expectations={4:"凌晨缺口可能高于通勤；提高容差会减少复核请求而非改变真实等待。",5:"随机日期更接近历史分布，不能替未来用途；小时/工作日均值或比全局均值更好。",6:"容量增大可能提高召回而带来误报，同一预测的MAE不变。",7:"补通勤可能改善通勤但不必改善总体；模型自产标签不会提供独立信息。"}
questions={4:"2011年第一季度早间哪些小时记录缺口需优先查来源？",5:"怎样评价后来日期的同小时租赁估计，相关日记录应怎样划分？",6:"每天只能人工查看2或5个高租赁提醒时，哪种规则有证据支持？",7:"预算96条真实训练标签优先补通勤是否优于随机？"}
for n,body in ((4,FOUR),(5,FIVE),(6,SIX),(7,SEVEN)):
    here=ROOT/f"lesson-{n:02d}"
    (here/'my_analysis.py').write_text(COMMON+body)
    (here/'my-config.json').write_text(json.dumps(configs[n],ensure_ascii=False,indent=2)+'\n')
    (here/'contract.json').write_text(json.dumps({"lesson":f"lesson-{n:02d}","question":questions[n],"user":"系统数据审查者" if n==4 else "小时估计的人工值班员","data_source":"UCI Bike Sharing CC BY4.0; 04小表人工模拟; 07标签生成规则模拟","metric":"覆盖率、分母或MAE次租赁/小时及本课用途规则","split_plan":"04仅日历元数据；05–07仅开发集13003+2208，测试目标未用","initial_expectation":expectations[n],"decisions":configs[n]},ensure_ascii=False,indent=2)+'\n')
    sub={"lesson":f"lesson-{n:02d}","status":"in_progress","report":f"lesson-{n:02d}/report.md","artifacts":[],"run":["python",f"lesson-{n:02d}/my_analysis.py"]}
    (here/'submission.json').write_text(json.dumps(sub,ensure_ascii=False,indent=2)+'\n')

NOTES = {
 4: "用途为2011第一季度早间缺口回查。自选小时范围和复核容差2/4；未观测不填零。凌晨383/450对通勤264/270；m4复核差3因容差改变标记。暂停推断未满足需求和缺行原因。小表是人工模拟，真实数据仅时点元数据。",
 5: "后来日期用途，选择时间验证与训练小时/工作日均值，合理对照全局均值；按日和按行随机作条件变化。时间MAE125.5385；随机按行69.9488却有617天跨两侧。按日2201行不能同记录比较；保留时间方案。INVALID组成恒等式排除合法比较，Bike无新人/新站ID。",
 6: "沿用05时间组均值。选择低估权重3及阈值350容量2；同预测合理对照容量5。MAE125.5385不变，召回124/733对186/733。容量0精确率null；2012-07-02选择17/18时，8时虽候选却FN。通勤441行误差更高，按资源采用容量5并保留限制。离线同日批次不是实时或因果效果。",
 7: "同一组均值作品，选择预算96与通勤/稀组优先；同初始240/预算/模型/评价随机对照。标签清单先落盘，无cnt进入选择，全部种子11/23/37报告。通勤优先总体三次均差，暂停稳定改进建议。规则生成96标签没有新独立观察，改变缺组回退不证明真效果；天气4验证0。回放不是新采集。",
}
for number in range(4, 8):
    here = ROOT / f"lesson-{number:02d}"
    command(["run", f"{number:02d}"])
    summary = json.loads((here / "artifacts/personal/summary.json").read_text())
    report = "# 我的研究报告\n\n" + NOTES[number] + "\n\n实验前预计、选择与来源见contract.json/my-config.json；个人程序为my_analysis.py。\n实际结果：\n```json\n" + json.dumps(summary, ensure_ascii=False, indent=2) + "\n```\n全部科学结果由python3 lesson-%02d/my_analysis.py重建，已列submission；测试目标未用。\n" % number
    (here / "report.md").write_text(report)
    submission = json.loads((here / "submission.json").read_text())
    submission["status"] = "complete"
    submission["artifacts"] = [p.relative_to(ROOT).as_posix() for p in sorted((here / "artifacts/personal").iterdir()) if p.is_file()]
    (here / "submission.json").write_text(json.dumps(submission, ensure_ascii=False, indent=2) + "\n")
    command(["check", f"{number:02d}"])
command(["ci"])
print(json.dumps({"scope":"simulated student workflow, not human teaching trial", "commands":COMMANDS,"deterministic_scientific_outputs":"four complete manifests rebuilt byte-for-byte by ci"}, ensure_ascii=False, indent=2))
_scratch.cleanup()
