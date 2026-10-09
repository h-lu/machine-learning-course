"""作者模拟开放选择的实跑；不是学生作业或真人试教。"""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent
ROOT=D.parents[2]/'course-student-template'
sys.path.insert(0,str(ROOT))
from mlcourse.bike_starter import load_development,mae,fit_simple_line,write_csv
train,val,audit=load_development(ROOT)
OUT=D/'open-project-smoke';OUT.mkdir(exist_ok=True)
actual=[r['cnt'] for r in val]
report={'scope':'作者模拟开放选择，非真人试教','training_n':len(train),'validation_n':len(val),'test_evaluated':False}
records=[]
# 自选温度回归，以及工作日条件组，公平对照训练均值。
a,b=fit_simple_line([r['temp'] for r in train],[r['cnt'] for r in train])
mean=sum(r['cnt'] for r in train)/len(train)
preds={'mean':[mean]*len(val),'candidate':[max(0,a+b*r['temp']) for r in val]}
report['choice']={'candidate':'simple temperature line','groups':'workingday','intercept':a,'slope':b}
report['mae']={k:mae(actual,p) for k,p in preds.items()}
report['groups']={str(g):{k:{'n':sum(r['workingday']==g for r in val),'mae':mae([r['cnt'] for r in val if r['workingday']==g],[z for r,z in zip(val,p) if r['workingday']==g])} for k,p in preds.items()} for g in [0,1]}
for method,p in preds.items():
 records.extend({'instant':r['instant'],'workingday':r['workingday'],'method':method,'prediction':z,'cnt':r['cnt'],'absolute_error':abs(z-r['cnt'])} for r,z in zip(val,p))

write_csv(OUT/'records.csv',records)
report['status']='passed'
(OUT/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
