# 操作支持：按问题查找

## 运行自己的配置

从学生仓库根目录执行。先复制本课config.json为my-config.json，只改你想比较的设置，再运行到新目录：

```bash
python3 scripts/sms.py run --config lesson-10/my-config.json --output lesson-10/artifacts/experiment-a
```

本课通常只改threshold（概率门槛，0到1）或capacity_fraction（本批最多复核的比例，0到1）。其他设置保持原值。比较门槛时可以读取已有records.csv的probability，按新门槛重新选人，无需重训；可用mlcourse.sms_course中的actions与metrics函数，也可自己计数。检查两方案的ID、概率和标签相同。

## 用输出核对自己的说法

|文件|含义与读法|
|---|---|
|records.csv|开发记录的id、label、probability、action；action=1是交复核|
|summary.json|n是分母；tp选对、fp误选、fn漏选、tn正确放过，precision查准率、recall召回率|
|prediction_trace.json|一条开发记录的x、weights逐项相乘，合计再加intercept；得到logit与probability|
|representation.json / model.npz|已学到的文字处理规则、分类系数与截距；不能在评价时重学|
|first_update.json / curve.csv|第一次改参数的细节、逐步曲线；第12课使用|

若选择别的ID，可让AI按同一模型输出它的计算过程，自己核对原文、ID和总和。`transform`只按已学规则转数字，`sigmoid`把得分转概率；它们在mlcourse/sms_course.py。不必抄完整的1200或384项，正文解释几项与总和，并给完整文件路径。

## 保存与重现

报告、问题说明和提交清单沿用原文件。run应指向自己的主要分析；artifacts列齐该命令的输出。默认已列八个文件，只是默认起点的清单，不代表做完比较。把status改为complete后可用`python3 scripts/course.py check 10`检查文件；本地`python3 scripts/course.py ci`在临时副本里删掉清单结果后重跑，核对字节是否一致。不要把运行耗时放进要求字节相同的结果。

非空输出目录会被拒绝，改用新目录而不是覆盖旧证据。空文本和未知词是允许检查的输入；NaN（无效数值）或非法设置应报错，先修正配置，不伪造结果。

所有拟合只用train，dev用于选择；最终留出仍按第14课约定。人工特征/词袋/TF–IDF和缓存后的分类训练只需NumPy；新文本编码的依赖须课前装好。英文缩写可查[阅读支架](../data/sms/READING.md)，保持模型实际收到的原文不变。
