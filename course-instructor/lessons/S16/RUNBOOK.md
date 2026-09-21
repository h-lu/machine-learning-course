# S16 教学运行单 · 怎样补充资料，而不是期待模型猜对

状态：已随 `ml-v13-course-map-2026-09-21` 于 2026-09-21 发布；本次没有真人 90 分钟试读。学生目录为 `lesson-18`。

## 主要关系与前置知识

主要关系是检索成功、回答受支持和任务完成必须分开。本课承接 S15：提示能规定资料不足时停止，却不能创造事实。学生无需会搜索引擎；关键词重合、阈值和逐字抽取均可核对。

## 课前准备与最小资源

```bash
python3 course-student-template/lesson-18/analysis.py --config course-student-template/lesson-18/config-start.json --output /tmp/S16-one
python3 course-student-template/lesson-18/analysis.py --config course-student-template/lesson-18/config-support.json --output /tmp/S16-two
```

阈值 1 时 dev-03 找对 D2 但任务未完成，故 failure_stage=answer；阈值 2 时 dev-02 找不到只有一个重合词的 D1，故 failure_stage=retrieval。两个失败用于课堂区分，不要求程序默认全对。

## 90 分钟组织

0–15 分钟读三份资料；15–28 分钟运行阈值 1；28–42 分钟手算一个重合分数并找两个失败；42–55 分钟阈值 2；55–70 分钟学生增加一条查询；70–75 分钟连续证据；75–90 分钟概念检查和提交。

巡视先让学生按 retrieval→answers→checks 的顺序读，不直接从总比例判断。看到来源编号时追问关键句是否真的回答问题。新增查询必须先写期望资料和答案要点，避免看输出后倒写。

## 必做成果与反馈

两种阈值、一次检索手算、检索失败、回答失败、资料不足、新查询与建议。路线可以保留阈值 1、采用阈值 2 或改切分，只要说明漏检与弱匹配后果。

环境故障先在纸上数词。JSON 错误按行列修复。修改资料后必须让回答重新读取新结果；不能复制旧 answers.csv。

## 概念检查

五点为切分、阈值、失败阶段、引用/支持、拒答取舍。题目不要求特定库或 API。
