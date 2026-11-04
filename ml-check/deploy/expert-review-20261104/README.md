# 32课题库审核修订

版本：`ml-expert-review-32-20261104-v1`。以`ml-lesson16-gpt-20261104-v1`为底稿，完整覆盖32课320题；历史课次、概念、题目ID和阶段时长保持一致。

- [教师审阅稿](REVIEW.md)：题目、选项、答案、逐项解析和学习提示。
- [独立内容复核](independent-review-after.md)：全题覆盖与四项最终修订。
- `runtime-validation.json`：5090上32课A→学习→B→反馈的真实应用流程。
- `build-browser.json`：32课两轮题目、桌面/手机共128组页面检查。
- `manifest.json`与`image-receipt.json`：题库哈希与仅新增题库层的镜像记录。

新课堂使用此版本；既有课堂继续使用其保存的题库快照。旧发布目录与应用默认历史测试夹具保持原文件。重新生成使用`python3 build_bank.py`；测试与构建统一在hblu-5090执行。
