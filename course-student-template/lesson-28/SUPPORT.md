# 第 28 课入门支持：从 Q02 重算即时与延迟后果

本路径使用现成状态、两条处理策略和完整命令。它与必做任务相同，不是额外练习。

### 五分钟内开始

```bash
python scripts/course.py start 28
python lesson-28/analysis.py --config lesson-28/config-start.json --output lesson-28/artifacts/start
```

成功后打开 `lesson-28/artifacts/start/trajectories.csv`，找到 `id=Q02` 的两行。先看 `policy` 和 `action`，确认 `fast_auto` 自动回答，`risk_aware` 转人工。

### 手算一条轨迹

候选配置把延迟伤害权重设为 4。Q02 自动回答的长期分数为 `1-4=-3`；转人工为 `1-0.5=0.5`。这里的分数来自本课规则，不是金钱。

### 只改延迟后果权重

先写哪个策略会在长期分数中胜出，然后运行：

```bash
python lesson-28/analysis.py --config lesson-28/config-support.json --output lesson-28/artifacts/support
```

打开 `summary.json` 的 `comparison`。起点与候选使用相同 8 条请求、相同状态和策略；权重从 1 变为 4。

### 自己检查一个条件

复制配置，只选择一项：删除状态中的 `risk`，或只改人工等待成本。

```bash
cp lesson-28/config-support.json lesson-28/config.json
python scripts/course.py run 28
```

报告 Q02 手算、8 条请求的总分、个人检查和奖励遗漏。实际完成后把 `submission.json` 改为 `complete`，再运行 `python scripts/course.py check 28`。
