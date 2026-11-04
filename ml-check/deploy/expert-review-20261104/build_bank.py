"""在hblu-5090生成32课修订快照；历史快照保持原文件。"""
import copy
import hashlib
import json
from pathlib import Path
import random
import re
from revisions import REWRITES, PAIRS, QUESTIONS

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "lesson16-gpt-20261104/lessons.json"
VERSION = "ml-expert-review-32-20261104-v1"
bank = json.loads(BASE.read_text())
original = copy.deepcopy(bank)
lessons = {lesson["lesson_id"]: lesson for lesson in bank["lessons"]}


def apply_pair(lesson, suffix, spec):
    title, context, a, b = spec
    concept = next(c for c in lesson["concepts"] if c["concept_id"].endswith("-" + suffix))
    concept.update(title=title, tutor_context=context)
    for phase, new in [("A", a), ("B", b)]:
        question = next(q for q in lesson["questions"] if q["concept_id"] == concept["concept_id"] and q["phase"] == phase)
        question.update(copy.deepcopy(new))


for key, pairs in REWRITES.items():
    for i, spec in enumerate(pairs, 1):
        apply_pair(lessons[key], f"{i:02d}", spec)
for (key, suffix), spec in PAIRS.items():
    apply_pair(lessons[key], suffix, spec)
questions = {q["id"]: q for lesson in bank["lessons"] for q in lesson["questions"]}
for key, new in QUESTIONS.items():
    questions[key].update(copy.deepcopy(new))

# 小范围措辞修订保持原答案含义。
def wording(qid, field, old, new):
    question = questions[qid]
    assert old in question[field], (qid, field, old)
    question[field] = question[field].replace(old, new)

wording("S27-B-05", "explanation", "质量下降仍有独立证据", "质量未达目标仍需检查")
wording("S29-A-02", "explanation", "这是另一个场景的结果，分母不同", "14/20=0.70，0.84与题中计数不符")
questions["S28-A-03"]["options"][1] = "把缓存命中时间当作模型重新计算时间"
for field in ["prompt", "explanation"]:
    questions["S25-B-03"][field] = questions["S25-B-03"][field].replace("空位提醒", "自习室提醒")
questions["S25-B-03"]["options"] = [text.replace("空位提醒", "自习室提醒") for text in questions["S25-B-03"]["options"]]
# 损失比较使用相同样例，原题的选项与答案继续成立。
questions["S17-A-04"]["prompt"] = "同三条固定训练问答更新前后的平均损失下降，但开发问题回答更容易漏掉依据。最合适怎样判断？"
questions["S17-A-04"]["options"] = ["只看训练损失就宣布全面改善", "只看训练轮数", "把开发问题加入训练后仍当独立评价", "训练拟合改善，开发回答的依据完整性仍需改进"]
questions["S17-A-04"]["answer"] = 3
questions["S17-A-04"]["reasons"] = ["训练拟合不能替代开发回答评价。", "轮数不直接说明质量。", "数据进入训练后用途已改变。", "两个观察量分别记录，比较条件明确。"]
question = questions["S11-B-54"]
question["prompt"] = "另一个模型最多保留128个词元。" + question["prompt"]
# 15课探索使用开发集，最终测试留到设置确定后。
for q in lessons["S13"]["questions"]:
    for field in ["prompt", "explanation"]:
        q[field] = q[field].replace("测试", "开发")
    if q["id"].endswith("-04"):
        q["options"] = [text.replace("测试", "开发") for text in q["options"]]
# 旧题中的容量措辞与现课代价评价统一。
for key in ["S10", "S11", "S12"]:
    lesson = lessons[key]
    for item in lesson["concepts"]:
        item["tutor_context"] = item["tutor_context"].replace("容量规则", "错误代价").replace("复核容量", "使用要求").replace("容量", "错误代价")
    for q in lesson["questions"]:
        q["options"] = [s.replace("复核容量", "错误代价").replace("容量", "错误代价") for s in q["options"]]
        q["explanation"] = q["explanation"].replace("复核容量", "使用要求").replace("容量规则", "错误代价")

# 独立审阅后的需求、开发选择与参数边界同步。
concept = next(c for c in lessons["S13"]["concepts"] if c["concept_id"] == "S13-05")
concept.update(title="开发选择与最终测试", tutor_context="用另一份开发集计算准确率并观察错分图。自由探索用开发结果选择隐藏层宽度，记录改动、图片和概率；设置确定后，用另留的测试集作一次最终评价。训练、开发和测试各有用途，当前分数仍是有限样本上的观察。")
questions["S13-B-05"]["options"][questions["S13-B-05"]["answer"]] = "记录这次探索，并用另留、未参与选择的测试集评价选定方案"
questions["S11-B-51"]["options"][questions["S11-B-51"]["answer"]] = "结合共同错误代价与开发预算比较"
next(c for c in lessons["S11"]["concepts"] if c["concept_id"] == "S11-51")["tutor_context"] = "用不同任务解释预训练知识迁移可能不匹配；比较表示时共同定义误判代价及开发预算，用本任务的结果判断。"
questions["S21-A-02"]["prompt"] = "用户只问办证材料和地点，一次调用D5已覆盖这两项，剩余调用预算为0。下一步最合适是什么？"
questions["S23-B-05"]["options"][questions["S23-B-05"]["answer"]] = "按工具允许范围修正请求参数，再调用"

# 用课程标题和模块统一学生目录。
TITLES = ["从数据到预测", "模型怎样从数据中学习", "怎样定义一个机器学习任务", "数据和标签是否适合这个任务",
"怎样划分数据并避免泄漏", "怎样评价数值预测", "怎样用有限预算改善训练数据", "输入表示怎样影响预测",
"线性模型、决策树与模型复杂度", "分类概率怎样变成行动", "文本怎样表示成数值", "损失、梯度与训练过程",
"预训练表示与迁移学习", "失败诊断与完整模型选择", "神经网络：计算与学习", "语言模型怎样利用上下文生成文本",
"怎样设计和比较提示", "检索怎样为生成提供资料", "怎样通过参数更新适配任务", "怎样评价开放式生成",
"怎样设计一个协作流程", "模型怎样调用工具", "智能体怎样根据反馈选择下一步", "怎样处理不可信资料与越权请求",
"怎样定位整个系统的失败原因", "何时自动完成、拒答或交给人", "怎样用不完整反馈学习", "强化学习：从奖励到策略更新",
"数据变化后怎样监测和更新模型", "怎样权衡质量、速度和资源", "新场景下怎样迁移和重新验证", "完成一个可解释、可复现的综合作品"]


def remap_explanation(text, mapping):
    # 显式选项引用换成新字母；“方案A/提示B”保留其原有方案含义。
    ordinals = {"1": "A", "2": "B", "3": "C", "4": "D", "一": "A", "二": "B", "三": "C", "四": "D"}
    text = re.sub(r"第([1234一二三四])项", lambda m: ordinals[m[1]] + "项", text)
    return re.sub(r"(?<![A-Za-z0-9])(?<!方案)(?<!提示)(?<!策略)(?<!模型)([ABCD])(?![A-Za-z0-9])", lambda m: mapping[m[1]], text)


changed_content = []
for n, lesson in enumerate(bank["lessons"], 1):
    old = original["lessons"][n-1]
    if lesson["questions"] != old["questions"] or lesson["concepts"] != old["concepts"]:
        changed_content.append(lesson["lesson_id"])
    lesson["title"] = TITLES[n-1]
    lesson["module"] = ("课程入门" if n <= 2 else "问题、数据与评价" if n <= 8 else "模型、表示与学习" if n <= 14
                        else "神经网络与生成模型" if n <= 20 else "工具与协作系统" if n <= 26 else "反馈、更新与综合应用")
    lesson["content_version"] = VERSION
    for concept in lesson["concepts"]:
        concept["tutor_context"] += " 请使用新的情境和数值，让学生先解释再核对；正式题目与答案留在作答阶段。"
    for phase in "AB":
        phase_questions = [q for q in lesson["questions"] if q["phase"] == phase]
        targets = [0, 1, 2, 3, (n + (phase == "B")) % 4]
        random.Random(f"{VERSION}-{lesson['lesson_id']}-{phase}").shuffle(targets)
        for question, target in zip(phase_questions, targets):
            old_options = question["options"][:]
            correct = question["answer"]
            order = [i for i in range(4) if i != correct]
            random.Random(question["id"]).shuffle(order)
            order.insert(target, correct)
            question["options"] = [old_options[i] for i in order]
            question["answer"] = target
            if "reasons" in question:
                reasons = question.pop("reasons")
                question["explanation"] = " ".join(f"{'ABCD'[j]}：{reasons[i]}" for j,i in enumerate(order))
            else:
                mapping = {"ABCD"[old]: "ABCD"[new] for new,old in enumerate(order)}
                question["explanation"] = remap_explanation(question["explanation"], mapping)
    (HERE / "source" / f"{lesson['lesson_id'].lower()}.json").write_text(json.dumps(lesson, ensure_ascii=False, indent=2) + "\n")

bank["version"] = VERSION
(HERE / "lessons.json").write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n")
lines = ["# 32课教师审阅稿", "", "每课五对A/B题。下列包含正式答案，保存在教师发布资料中。", ""]
for n, lesson in enumerate(bank["lessons"],1):
    lines += [f"## {n:02d} {lesson['title']}（{lesson['lesson_id']}）", ""]
    for concept in lesson["concepts"]:
        lines += ["### " + concept["title"], "", "学习提示：" + concept["tutor_context"], ""]
        for q in lesson["questions"]:
            if q["concept_id"] == concept["concept_id"]:
                lines += [f"**{q['id']}** {q['prompt']}", ""]
                lines += [f"{'ABCD'[i]}. {o}" for i,o in enumerate(q["options"])]
                lines += ["", "答案：" + "ABCD"[q["answer"]], "", q["explanation"], ""]
(HERE / "REVIEW.md").write_text("\n".join(lines))
manifest = {"version": VERSION, "base_version": original["version"], "base_sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
            "changed_content_lessons": changed_content, "changed_lessons": [l["lesson_id"] for l in bank["lessons"]],
            "lesson_count": 32, "question_count": 320, "ids_and_durations_preserved": True,
            "files": {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/"lessons.json", *sorted((HERE/"source").glob("*.json"))]}}
(HERE / "manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
print("Built", VERSION, "content revisions:", ",".join(changed_content))
