# S17 入门支持：在同样案例上选适配路线


以下命令都在学生仓库根目录执行，也就是能同时看到 `scripts` 和本课目录的位置；不要在 Python 的 `>>>` 中输入。电脑只识别 `python3` 时，把命令开头的 `python` 换成 `python3`。
本页完成的是本课 Core，不需要另外训练大模型。第一项小任务：在纸上列三行“提示、上下文、参数”，分别写是否更新参数、需要什么新增数据。

## 1. 比较提示与上下文

```bash
python scripts/course.py start 19
python lesson-19/analysis.py --config lesson-19/config-start.json --output lesson-19/artifacts/prompt-vs-context
```

先看 `route_comparison.csv`。两条路线都在 6 个案例上评价。提示路线任务完成约 `4/6`、资料支持约 `2/6`、准备时间 10 分钟；上下文路线三项中任务与资料支持均为 `6/6`，准备时间 25 分钟。时间是课程人工估计，不能当实测运行耗时。

再看 `case_scores.csv`：`case-01` 需要精确截止时间，提示路线没有新事实；上下文路线引用 D1。`case-02` 没有资料，两条路线都停止。解释这些案例比只报平均更重要。

## 2. 比较提示与参数候选

```bash
python lesson-19/analysis.py --config lesson-19/config-support.json --output lesson-19/artifacts/prompt-vs-parameter
```

参数候选任务完成约 `5/6`，资料支持约 `1/6`，使用 12 条适配样例，准备时间 60 分钟。它能在固定案例中给出一些任务答案，却把“训练样例”写成来源；这不是可核对的课程资料。

这些是已有固定候选输出。`parameters_updated=True` 来自材料说明，本课没有训练日志，不能写成自己已经重现实验。

## 3. 选择自己的两条路线

从任一配置另存 `config-mine.json`，只列两个不同路线编号。先写使用条件，例如“课程规则经常更新，所以事实支持比短准备时间更重要”，再运行：

```bash
python -m json.tool lesson-19/config-mine.json
python lesson-19/analysis.py --config lesson-19/config-mine.json --output lesson-19/artifacts/my-routes
```

若写入不存在的路线，程序会拒绝。要研究新提示或新问题，必须先为所比较路线准备对应新输出；不能让旧 `case_scores.csv` 代替。

## 4. 串联证据

报告引用：S15 哪份文件说明提示对格式或停止回答有帮助；S16 哪份文件说明资料可找到但回答仍可能失败；本课哪两个案例支持最终路线。不同课的数据不相同，不把比例直接相减。

## 5. 检查提交

保存两组比较和个人选择，填写任务说明，最终 `config.json` 必须列出你采用的两个候选。完成后：

```bash
python scripts/course.py run 19
python scripts/course.py check 19
```

程序失败时先检查路线拼写。固定材料缺少新输入时，正确做法是报告没有匹配结果，而不是复制最相似的一条回答。
