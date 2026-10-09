"""C02教师选择的一条真实参考路线；独立核算，不规定学生答案。"""
from pathlib import Path
import csv
import hashlib
import json
import math
import argparse
D = Path(__file__).resolve().parent
ROOT = D.parents[2]
source = ROOT / "course-student-template/data/bike/hour.csv"
expected = "e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f"
assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
with source.open(encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))
train = [r for r in rows if r["dteday"] < "2012-07-01"]
val = [r for r in rows if "2012-07-01" <= r["dteday"] < "2012-10-01"]
assert (len(train), len(val), len(rows)-len(train)-len(val)) == (13003, 2208, 2168)
y = [int(r["cnt"]) for r in val]
x = [float(r["temp"]) for r in val]
mean = math.fsum(int(r["cnt"]) for r in train) / len(train)
def metrics(pred, hour=None):
    ids = [i for i,r in enumerate(val) if hour is None or int(r["hr"])==hour]
    return {"n":len(ids),"mae":math.fsum(abs(pred[i]-y[i]) for i in ids)/len(ids),
            "underestimated_rows":sum(pred[i] < y[i] for i in ids)}
report = {"lesson":"C02","data_sha256":expected,"train_n":len(train),"validation_n":len(val),
          "sealed_test_rows":2168,"test_evaluated":False,"scope":"教师参考路线，非学生唯一答案"}
if 2 == 1:
    for slope in [300.,450.]:
        pred = [max(0.,30+slope*a) for a in x]
        report[str(slope)] = {"metrics":metrics(pred),"hours":{str(h):metrics(pred,h) for h in [3,17,23]},
         "first_three":[{"instant":val[i]["instant"],"prediction":pred[i],"cnt":y[i],"absolute_error":abs(pred[i]-y[i])} for i in range(3)]}
    assert math.isclose(report["300.0"]["metrics"]["mae"],175.44972826086956,abs_tol=1e-9)
    assert report["450.0"]["metrics"]["mae"] > report["300.0"]["metrics"]["mae"]
    assert report["450.0"]["hours"]["17"]["mae"] < report["300.0"]["hours"]["17"]["mae"]
elif 2 == 2:
    tx=[float(r["temp"]) for r in train];ty=[int(r["cnt"]) for r in train]
    xm=math.fsum(tx)/len(tx)
    slope=math.fsum((a-xm)*(b-mean) for a,b in zip(tx,ty))/math.fsum((a-xm)**2 for a in tx)
    intercept=mean-slope*xm
    preds={"mean":[mean]*len(y),"temp_linear":[max(0.,intercept+slope*a) for a in x]}
    report["training_sum"]=sum(ty);report["model"]={"mean":mean,"intercept":intercept,"slope":slope}
    report["methods"]={m:{"metrics":metrics(p),"hours":{str(h):metrics(p,h) for h in [8,17,23]}} for m,p in preds.items()}
    assert math.isclose(report["methods"]["mean"]["metrics"]["mae"],197.82937894348797,abs_tol=1e-9)
    assert math.isclose(report["methods"]["temp_linear"]["metrics"]["mae"],174.29402691551385,abs_tol=1e-9)
else:
    p=[max(0.,30+300*a) for a in x]
    for t in [200,260]:
        pairs=[(a>=t,b>=t) for a,b in zip(p,y)]
        counts={"true_positive":sum(a and b for a,b in pairs),"false_positive":sum(a and not b for a,b in pairs),
                "false_negative":sum(not a and b for a,b in pairs),"true_negative":sum(not a and not b for a,b in pairs)}
        assert sum(counts.values())==len(val)
        report[str(t)]={"counts":counts,"predicted_alert_rows":sum(a for a,b in pairs),"mae":metrics(p)["mae"],
                         "actual_high_threshold":t}
    assert report["200"]["mae"] == report["260"]["mae"]
    assert report["200"]["counts"]=={"true_positive":1247,"false_positive":728,"false_negative":72,"true_negative":161}
    assert report["260"]["counts"]=={"true_positive":346,"false_positive":115,"false_negative":745,"true_negative":1002}
report["status"]="passed"
parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,default=D/"verification.json")
args=parser.parse_args()
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
