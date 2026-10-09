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
# 自选规则和自选失败小时；不由完整课例工具执行。
pred=[max(0,25+280*r['temp']) for r in val]
report['choice']={'input':'temp','intercept':25,'slope':280,'failure_hours':[8,20]}
report['mae']=mae(actual,pred)
report['groups']={str(h):{'n':sum(r['hr']==h for r in val),'mae':mae([r['cnt'] for r in val if r['hr']==h],[p for r,p in zip(val,pred) if r['hr']==h])} for h in [8,20]}
records=[{'instant':r['instant'],'hr':r['hr'],'temp':r['temp'],'prediction':p,'cnt':r['cnt'],'absolute_error':abs(p-r['cnt'])} for r,p in zip(val,pred)]

write_csv(OUT/'records.csv',records)
report['status']='passed'
(OUT/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
