# 第14课｜按需运行帮助

## 一个条件的起点
沿用原学生仓库、Python和NumPy环境，不新建第二个课程仓库：

```sh
python3 lesson-14/analysis.py
```

默认只有一个条件。复制config.json为my-config.json，按自己的问题改设置后：

```sh
python3 lesson-14/analysis.py --config lesson-14/my-config.json --output lesson-14/artifacts/my-run
```

不要用非空旧目录，防止覆盖证据。manual/bow/tfidf沿用第11、12课字段；pretrained只接受分类器训练与行动字段，不接受min_df/token_pattern等词表设置。

## 八个输出怎么看
config.json是实际设置；representation.json是输入转换；model.npz存系数；summary.json给dev指标；records.csv一行一条dev短信；prediction_trace.json追踪一条记录；first_update.json给第一次更新；curve.csv一行一步训练状态。

TP选对、FP误选、FN漏选、TN正确放过；precision=TP/(TP+FP)，recall=TP/(TP+FN)。分母为零时为未知，不伪装为完美。action是复核选择，不等于真实标签。

## 选定系统后交教师评价

```sh
python3 lesson-14/lock_system.py --run lesson-14/artifacts/my-run --output lesson-14/artifacts/selected --reason "写自己的开发证据和选择理由"
```

selected中是参数、配置、摘要和system_lock.json。它只保存你选的方案，不会帮你挑最好。把这一目录交教师，使用独立最终数据返回final_records.csv、final_result.json。日常run只重建开发实验，不把教师最终评价写成反复执行的命令。

如果目录改变、代码或数据变动，评价会拒绝；先核对原因，不手改清单。一次性标记不是保密系统，更换目录仍不能使已看过数据重新独立。已有第13课结果可以直接定案，不必重新训练以满足形式。

## 提交前
把自己的全部开发比较命令写入一个脚本，run以命令参数列表指向它，artifacts列它生成的确定性文件；不要列运行耗时。设置status=complete，运行check/ci。ci在临时副本重建，不替你核对研究解释，也不应重复读取最终留出。

`submission.json`沿用原格式：lesson为`lesson-13`或`lesson-14`，report为报告相对路径，run为参数列表，例如 `["python3", "lesson-13/my-analysis.py"]`，不是一个shell字符串。
