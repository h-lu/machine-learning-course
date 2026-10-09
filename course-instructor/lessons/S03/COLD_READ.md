# 第05课操作核对与冷读边界

日期2026-10-09；受检路径为独立ml-course-redesign副本，不是原项目或线上发布。执行者为已了解教师参考的开发者，因此是按学生页进行的模拟操作核对，**不是盲读或真人试读**，不证明真实学生自主完成用时。

## 学生页操作证据

README首屏明确自主问题/至少两个重要决策；第三节课堂任务，无分钟/预计用时；SUPPORT按卡点可选，不要求统一顺序。阅读LEARN不同小表的完整例题后，按输入卡点运行：从学生仓库根`python3 lesson-05/analysis.py --config lesson-05/config.json --output lesson-05/artifacts/cold-starter-a`。

实际退出0，先看summary训练/验证计数与sample一行；起点status=not_started、sample12行。04/05 sample仅元数据无cnt；06/07没有capacity排名、抽样策略或学习曲线。起点只准备数据，正式标准分析须学生自主构建。Python3.14/NumPy2.5本机，单起点命令约0.21–0.22秒是作者运行时间，不是学生学习预计。

## 修改与仍需支持

撤掉早期逐步菜单recipe与学生时间表；完整基础例题保留但不提供正式分析结果。默认submission只是起点占位，学生须增加自己科学结果与重建命令；只跑起点不认定项目完成。04来源/代理/复核/AI独立核恢复核心，05对象分组核心不放拓展，07AI标签与真实证据核心保留。

已实际核：本课starter命令、页结构/路径、必要产物，教师可选完整例的独立数学见OWNED04_07_VALIDATION.json。未做：真实学生试教、自拟问题的所有分析路径、线上新题发布、付费/网络模型资源。不能把已核片段称整课所有可能路线通过。

## 本次起点文件字节记录

```json
{
  "summary.json": "ed46a3ff9794b95733af900a089ef11e91ef360e72e60736ba5413cb31f4115d",
  "sample.csv": "03e772320c8ca05d70b2621c4a82ba710afbd32e5483a153292cb4e1ef3b2c04",
  "split_manifest.csv": "8ef028447e2af4998265e40673103ae7ad004486c8e560afb34e2a904cab9ffc",
  "config_snapshot.json": "ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356",
  "audit.json": "580c6d4784d1b8183b0930e6e8b6f710c24931f9e51a8ea4b3404179b8399def"
}
```

追加实跑：按SUPPORT修正ROOT/sys.path再import的my_analysis入口探针，四课各退出0，读取13,003训练/2,208验证，只打印计数；临时探针移除，未生成正式学生分析答案。
