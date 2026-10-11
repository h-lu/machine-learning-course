# 操作支持

Python命令从学生仓库根目录运行；已验证的环境见数据说明。输出目录必须是新的，防止覆写比较证据。submission.json只列自己确实使用的入口和结果。

可选完整模型代码在mlcourse/bike_models09.py，命令 `python3 lesson-09/analysis.py --compare --output lesson-09/artifacts/example`。这是供阅读修改的拟合示例，不替你选择失败问题或给结论。compare的fields参数同时供两方使用；depth限制树层数。trace.json保存线性各项贡献与树路径。若自己改字段，保持允许的同小时信息；禁止cnt的组成项、标识号和未来信息。analysis.py --compare读取config.json中的共同fields和depth，也可--config指定新的配置；树的候选阈值来自训练输入的19个分位位置，不声称穷举全部切点。

使用--compare后，除summary.json和records.csv外还会生成trace.json；把它加入submission.json的artifacts并更新run，才能按原逐文件重现流程验证。
