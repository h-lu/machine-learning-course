# 第14课｜运行帮助

以下命令在学生仓库根目录执行，沿用已有Python与NumPy环境。预训练表示的缓存和本地模型沿用第13课；处理新英文的依赖见[第13课运行准备](../lesson-13/SUPPORT.md#运行前准备)。

## 运行开发实验

```sh
python3 lesson-14/analysis.py
```

默认使用TF–IDF，结果在 `lesson-14/artifacts/baseline/`。也可以直接沿用第13课已有结果。

需要另一个条件时，复制 `lesson-14/config.json` 为 `lesson-14/my-config.json`，按问题修改后运行：

```sh
python3 lesson-14/analysis.py --config lesson-14/my-config.json --output lesson-14/artifacts/my-run
```

每次使用新的输出目录。manual、bow、tfidf沿用第11、12课字段；pretrained使用固定表示，配置只保留分类器训练和行动设置，可从第13课config.json复制起步。

## 阅读输出

|文件|用途|
|---|---|
|config.json|本次设置|
|representation.json|输入转换信息|
|model.npz|分类器系数|
|summary.json|dev指标及分母|
|records.csv|每条dev短信的预测与行动|
|prediction_trace.json|一条记录的完整计算|
|first_update.json|第一次参数更新|
|curve.csv|训练过程|

先在summary.json核对FP、FN等错误数，再用records.csv按ID对齐两个方案，最后用prediction_trace.json追踪具体计算。action表示是否进入复核名单，真实类别由标签表示。

## 保存选定系统

完成开发比较后，指定实际选中的实验目录：

```sh
python3 lesson-14/lock_system.py --run lesson-14/artifacts/my-run --output lesson-14/artifacts/selected --reason "写自己的开发证据和选择理由"
```

若选择默认结果，将run路径换为 `lesson-14/artifacts/baseline`；若选择第13课结果，填其对应目录。

selected包含参数、配置、摘要和system_lock.json文件指纹清单。将该目录交教师，获得final_records.csv与final_result.json。若提示代码、数据或文件不一致，核对版本与来源，保持定案清单与实际内容对应。

## 提交检查

将自己的开发实验命令写入脚本，在 `submission.json` 中以参数列表登记 `run`，例如 `["python3", "lesson-14/my-analysis.py"]`；`artifacts`登记脚本生成的确定性产物。教师最终评价文件单独保留，不放入反复执行的开发命令。

完成后设 `status=complete`，运行：

```sh
python3 scripts/course_l1314.py check 14
python3 scripts/course_l1314.py ci 14
```

`ci`在临时副本中重建登记的开发产物，检查可复现性。
