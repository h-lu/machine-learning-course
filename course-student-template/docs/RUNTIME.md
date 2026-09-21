# 小实验的运行办法

所有命令都在学生仓库根目录执行，也就是能同时看到 `scripts`、`lesson-01` 和 `lesson-32` 的目录。需要 Python 3.10 以上；开课前安装依赖，课堂实验不需要联网。

```bash
python3 -m pip install -r requirements.txt
```

每课的 `analysis.py` 是起步程序，`config.json` 是默认配置，`artifacts/` 是默认结果目录。最稳妥的入口是当课 README 或 SUPPORT 给出的命令；不同课的参数和输出文件不完全相同。

## 先跑通一次

例如，第 9 课的独立分析程序支持 `--config`、`--output` 和 `--split`，不支持 `--data`：

```bash
python3 lesson-09/analysis.py --config lesson-09/config.json --output lesson-09/artifacts/trial
```

成功后先按第 9 课 README 打开 `comparison.csv`，再看 `records.csv` 和 `outside_check.csv`。要查某一课实际支持的参数，可运行：

```bash
python3 lesson-09/analysis.py --help
```

`--output` 接受一个目录路径。比较两个设置时，请写入两个不同的目录，避免新结果和旧结果混在一起。相对路径从执行命令的仓库根目录解释。

## 两类运行入口

### 第 1–8 课：共享运行时

第 1–8 课的 `analysis.py` 调用 `mlcourse/runtime.py`。这些课支持：

- `--config`：选择 JSON 配置文件；
- `--data`：选择 JSON 数据文件；
- `--output`：选择结果目录；
- 部分课支持 `--split validation` 或 `--split test`，具体以当课 README 为准。

共享运行时会生成 `summary.json`，并按课次生成 `records.csv`、`comparison.csv` 等表格。`summary.json` 中的 `metrics`、`comparison`、`stress_test`、`details` 和 `provenance` 是这类早期课程的共享结构。第 1–8 课的具体字段和单位见各课 `data/DATA.md`。

### 第 9–32 课：按课分析程序

第 9–32 课使用各课自己的 `analysis.py`。所有这些程序都支持 `--config` 和 `--output`，但只有需要替换数据的课才支持 `--data`；个别课还有 `--split` 或其他参数。不要把某一课的命令行原样套到另一课。

输出表格围绕当课问题命名，例如 `attention_weights.csv`、`responses.csv` 或 `dimension_scores.csv`。`summary.json` 的字段也会随课次变化，没有一套适用于第 9–32 课的固定字段。运行后先打开当课 README 或 SUPPORT 点名的文件和行，再用 `data/DATA.md` 解释列名。

## `course.py` 运行的是哪条命令

```bash
python3 scripts/course.py run 17
```

`scripts/course.py` 不会自行猜测配置；它会逐项执行当课 `submission.json` 的 `run` 列表。`check` 只检查清单所列结果是否存在，`ci` 还会在临时副本中删除这些结果、重新运行，并比较文件哈希。这些检查能证明文件可重建，不会自动评价报告中的理由是否充分。

第 17、18、20 和 26 课把开发数据与最终评价数据放在不同文件中。仓库默认的 `submission.json` 只运行开发数据；它不会读取 `data/final.json` 或 `data/holdout.json`。只有在开发数据上选好方案、写好评价规则并固定 `config-final.json` 之后，才按当课 README 把 `submission-final.json` 复制为 `submission.json`，再运行 `course.py run`。这样 `run`、`check` 和 `ci` 都指向同一份最终评价结果。

最终数据在公开教学仓库中仍可被人主动打开，所以这个设计练习的是正确的使用顺序，不是技术保密。如果提前看过最终数据或结果，就在报告中说明，并把它改称为开发证据。

## 结果、哈希和限制

输入、配置和程序哈希可以帮助发现文件是否发生变化，但不能证明数据来源真实或结论正确。JSON 不写入 NaN 或 Infinity；暂时无法定义的数值应写为 `null` 并说明原因。课程提供的起步结果是核对示例，不是学生的采用建议，也不能代替自己的对照和理由。

课程数据都是教学数据，不代表真实人群、机构或线上业务。神经网络课使用小型 NumPy 实现；表示、语言模型和问答课会区分人工数值、微型模型、固定候选输出与真实预训练模型。使用固定材料只能评价材料覆盖的候选，不能声称测试了没有实际生成的新提示或新模型。

## 开发者回归检查

以下命令用于确认课程自带程序的计算、输入处理和确定性；学生替换方法后，需要为新方法设计对应检查。

```bash
python3 -m unittest discover -s tests -v
```

要检查第 1–8 课的教学数据如何生成，可读 `scripts/build_example_data.py`。下面的命令在新目录重建示例，不覆盖当前课次修改：

```bash
python3 scripts/build_example_data.py --output /tmp/ml-example-data
```

重建目录只包含示例数据、配置和入口样例；实际运行仍需要完整学生仓库中的 `mlcourse/`。
