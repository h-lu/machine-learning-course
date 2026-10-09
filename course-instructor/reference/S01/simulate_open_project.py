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
# 自选前一天日历任务与提醒210/330；实际高需求标准固定300。
pred=[max(0,15+18*r['hr']) for r in val]
report['choice']={'purpose':'calendar-only previous-day estimate','input_fields':['hr'],'rule':'15+18*hr','alert_thresholds':[210,330],'actual_high_threshold':300}
report['mae']=mae(actual,pred);report['decision']={}
for threshold in [210,330]:
 pairs=[(p>=threshold,y>=300) for p,y in zip(pred,actual)]
 counts={'tp':sum(a and b for a,b in pairs),'fp':sum(a and not b for a,b in pairs),'fn':sum(not a and b for a,b in pairs),'tn':sum(not a and not b for a,b in pairs)}
 assert sum(counts.values())==len(val)
 report['decision'][str(threshold)]=counts
 records.extend({'instant':r['instant'],'hr':r['hr'],'threshold':threshold,'prediction':p,'cnt':y,'alert':a,'actual_high':b} for r,p,y,(a,b) in zip(val,pred,actual,pairs))

write_csv(OUT/'records.csv',records)
report['status']='passed'
(OUT/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
