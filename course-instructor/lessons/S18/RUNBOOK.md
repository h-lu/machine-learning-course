# S18 教学运行单 · 没有唯一答案时，怎样判断真的变好了

状态：已随 `ml-v13-course-map-2026-09-21` 于 2026-09-21 发布；本次没有真人 90 分钟试读。学生目录为 `lesson-20`。

## 主要关系与前置知识

本课收束六课作品：开放回答需分维度评价，评分规则本身也要检查。学生已见提示、检索和路线选择；本课不再改变生成方案，而是评价已有候选。两份评分和 proxy 分数均为课程构造，不测试真实 AI 能力。

## 课前准备与最小资源

```bash
python3 course-student-template/lesson-20/analysis.py --config course-student-template/lesson-20/config-start.json --output /tmp/S18-ab
python3 course-student-template/lesson-20/analysis.py --config course-student-template/lesson-20/config-support.json --output /tmp/S18-ba
```

核对 dev-01,A 的 1.1；`disagreements.csv` 有 dev-02/B 任务完成、dev-03/B 格式、dev-04/A 事实三项分歧。换顺序后人工加权总分不变，固定 proxy 分数变化。

## 90 分钟组织

0–15 分钟定义四维度；15–30 分钟运行与手算；30–43 分钟讨论一个分歧；43–55 分钟交换顺序；55–67 分钟确定权重后运行 final；67–75 分钟六课证据链；75–90 分钟概念检查和提交。

巡视不先问谁总分高，而问哪个维度失败、证据在哪。学生只取平均时让其提出一句量表澄清。权重须在 final 前写用途理由，不因喜欢某候选而调整。

## 必做成果与反馈

四维度定义、一项加权手算、一项分歧处理、顺序对照、个人权重、final、六课证据和最终建议。评价结果可以支持保留原路线或暂缓，不要求宣称改进。

学生看过 final 后改权重时保留过程，将 final 降为开发证据。真实试教可邀请两名学生独立评分，但必须与课程模拟标注分开记录。

## 概念检查

五点为分维度、量表、评分分歧、评价偏差、开发/最终。数值题分母和权重明确，B 题检查迁移而非背答案。
