"""S13：用可追踪的小实验区分固定基础分数、输入变化与参数更新。"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
HERE = Path(__file__).resolve().parent

def read_json(path): return json.loads(path.read_text(encoding="utf-8"))
def sigmoid(value):
    if value >= 0: return 1.0/(1.0+math.exp(-value))
    e=math.exp(value); return e/(1.0+e)
def log_loss(rows,scores):
    values=[]
    for row,score in zip(rows,scores,strict=True):
        p=min(max(score,1e-9),1-1e-9); y=row["label"]
        values.append(-(y*math.log(p)+(1-y)*math.log(1-p)))
    return sum(values)/len(values)
def metrics(rows,scores):
    correct=sum((score>=0.5)==bool(row["label"]) for row,score in zip(rows,scores,strict=True))
    return {"n":len(rows),"accuracy":correct/len(rows),"log_loss":log_loss(rows,scores)}
def write_csv(path,rows):
    with path.open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",type=Path,default=HERE/"config.json")
    parser.add_argument("--data",type=Path,default=HERE/"data/base.json")
    parser.add_argument("--output",type=Path,default=HERE/"artifacts")
    args=parser.parse_args(); data,config=read_json(args.data),read_json(args.config)
    rows=data["rows"]; train=[r for r in rows if r["split"]=="train"]; evaluation=[r for r in rows if r["split"]=="evaluation"]
    steps=int(config["head_steps"]); learning_rate=float(config["learning_rate"])
    if not 1<=steps<=10000 or not 0<learning_rate<=2: raise SystemExit("head_steps 应在 1—10000，learning_rate 应在 (0, 2]。")
    bias,weight=0.0,1.0; trace=[]
    for step in range(steps+1):
        if step in {0,1,steps//2,steps}:
            scores=[sigmoid(bias+weight*(r["pretrained_score"]-0.5)) for r in train]
            trace.append({"step":step,"bias":bias,"weight":weight,"train_log_loss":log_loss(train,scores)})
        if step==steps: break
        gb=gw=0.0
        for r in train:
            feature=r["pretrained_score"]-0.5; error=sigmoid(bias+weight*feature)-r["label"]
            gb+=error; gw+=error*feature
        bias-=learning_rate*gb/len(train); weight-=learning_rate*gw/len(train)
    base_scores=[r["pretrained_score"] for r in evaluation]; context_terms=set(config["context_terms"])
    context_scores=[min(.99,max(.01,r["pretrained_score"]+(config["context_boost"] if context_terms.intersection(r["tokens"]) else 0.0))) for r in evaluation]
    head_scores=[sigmoid(bias+weight*(r["pretrained_score"]-0.5)) for r in evaluation]
    routes=[
      {"route":"fixed_record","changed_input":False,"changed_parameters":False,**metrics(evaluation,base_scores)},
      {"route":"input_context_rule","changed_input":True,"changed_parameters":False,**metrics(evaluation,context_scores)},
      {"route":"trained_output_head","changed_input":False,"changed_parameters":True,**metrics(evaluation,head_scores)}]
    records=[]
    for r,base,context,head in zip(evaluation,base_scores,context_scores,head_scores,strict=True):
        records.append({"id":r["id"],"text":r["text"],"label":r["label"],"fixed_score":round(base,6),"context_score":round(context,6),"head_score":round(head,6),"context_rule_fired":bool(context_terms.intersection(r["tokens"]))})
    args.output.mkdir(parents=True,exist_ok=True); write_csv(args.output/"routes.csv",routes); write_csv(args.output/"records.csv",records); write_csv(args.output/"parameter_trace.csv",trace)
    evidence={"product":data["product"],"stage":"S13-capability-source","evidence_kind":"固定基础分数观察 + 微型输出头机制实验","supports":["输入变化可以不更新参数","输出头训练会改变输出头参数","三条路线可以在相同评价记录上比较"],"does_not_support":["这些固定分数来自真实预训练模型","输出头训练等于预训练或完整微调","当前准确率能代表真实学生问题"],"next_lesson":"S14 将用微型注意力数值检查信息可见性。"}
    (args.output/"evidence.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary={"lesson":"S13","status":"example_only","config":config,"routes":routes,"trained_head":{"initial":{"bias":0.0,"weight":1.0},"final":{"bias":bias,"weight":weight}},"provenance":{"data_file":args.data.name,"config_file":args.config.name,"data_sha256":hashlib.sha256(args.data.read_bytes()).hexdigest(),"config_sha256":hashlib.sha256(args.config.read_bytes()).hexdigest(),"entry_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},"limits":evidence["does_not_support"]}
    (args.output/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"S13：已写入 {args.output}。先看 routes.csv，再看 parameter_trace.csv 和 evidence.json。")
if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as error:
        raise SystemExit(f'无法运行：{error}\n请检查配置、数据字段和 JSON 格式；旧输出不能作为本次运行结果。') from None
