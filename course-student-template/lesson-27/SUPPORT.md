# 第 27 课入门支持：先看一次选择真正留下了什么

这是一条完成必做任务的路径。所有命令都在学生仓库根目录运行，不需要先写代码。

### 五分钟内得到第一份结果

```bash
python scripts/course.py start 27
python lesson-27/analysis.py --config lesson-27/config-start.json --output lesson-27/artifacts/start
```

成功标志是终端显示 `S25 已生成`，并出现 `summary.json`、`rounds.csv`、`episodes.csv`。若失败，先确认当前位置能看到 `scripts` 和 `lesson-27`，保存完整报错。

### 第一眼看哪里

打开 `rounds.csv`，筛选 `seed=3`、`policy=epsilon`。先看第一行的 `chosen_response`、`observed_feedback` 和 `other_response_feedback`。最后一列必须写“未观察”，因为这一轮没有展示另一回答。

数出这一组 16 行，把 `observed_feedback` 相加后除以 16。单位是每轮平均反馈。再数 `brief` 和 `guided` 各出现多少次，两数之和应为 16。

### 只改探索率

先在报告写预计：“探索率从 0.10 增至 0.25，我预计带步骤回答会被尝试更多／更少，平均反馈可能……”。运行：

```bash
python lesson-27/analysis.py --config lesson-27/config-support.json --output lesson-27/artifacts/support
```

两个配置的种子和反馈表相同。比较五个种子，不能只选一个结果。`episodes.csv` 每行代表一个策略在一个种子下的 16 轮。

### 作出自己的选择

复制配置并只改探索率：

```bash
cp lesson-27/config-support.json lesson-27/config.json
python scripts/course.py run 27
```

在 `report.md` 写反馈、覆盖、短期代价、模拟限制和建议。完成后再把 `submission.json` 改为 `complete`，运行 `python scripts/course.py check 27`。
